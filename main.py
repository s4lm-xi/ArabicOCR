import cv2
import numpy as np
import matplotlib.pyplot as plt
from pdf2image import convert_from_path
from scipy.ndimage import interpolation as inter
from PIL import Image as im
import os
from tqdm import tqdm
import time
import shutil
import argparse




def findBaseLine(img, thresh):
    # Threshold the image
    # Get image shape
    (h,w) = thresh.shape
    # Save potential baselines with their zeros count
    baseline_row = []
    # Define percentage, finetune accordingly
    percent = 50

    # Iterate over all rows in the image
    for row in range(0, h):
        # Get amount of black pixels in a single image row
        count = w - np.count_nonzero(thresh[row, :]) 
        # If the count of black pixels is more than the percent% less of the image width. Append it
        if count >= w - (percent / 100 * w):
            baseline_row.append([count, row])
            

    # Find baseline and black count using "max"
    count, baseline = max(baseline_row)
    # Draw a line to visualize baseline
    cv2.line(img, (0, baseline), (h, baseline), (0,255,0), 1)
    cv2.imwrite('baseline.jpg', img)
    # show
    #plt.imshow(img)
    return count, baseline



def splitWhiteSpaces(thresh):
    white_cut = []

    (h,w) = thresh.shape
    # Iterate over all the columns
    for col in range(w):
        # Get count of all white pixels
        white_count = np.count_nonzero(thresh[:, col])
        # Check if the count of white pixels is equals to the image total height to determine if it contains all white pixels
        if white_count == h:
            # Make sure the column index in not over (Width -5) to not store unnecessary column indexes
            if not col >= (w - 5):
                white_cut.append(col)
                # Fill column with black pixels just for visualization
                #thresh[:, col] = [0 for i in range(h)]

                
    # Save all filtered white columns where a "CUT" should not happen
    increment = 1
    to_remove = set()
    for x in white_cut:
        if x not in to_remove:
            for i in range(1, 1 + increment):
                to_remove.add(x - i)
                to_remove.add(x + i)
                
    final = [x for x in white_cut if x not in to_remove]
    # Perform white column cuts and save the images
    for index, cut in enumerate(final):
        if index == 0 and len(final) > 1:
            cv2.imwrite(f'chars/{index}.jpg', thresh[:, 0:cut])
            
        # If only one cut is found split the image in 2 halves and save them both
        elif index == 0 and len(final) == 1:
            cv2.imwrite(f'chars/{index}.jpg', thresh[:, 0:cut])
            cv2.imwrite(f'chars/{index+1}.jpg', thresh[:, cut:])
        else:
            cv2.imwrite(f'chars/{index}.jpg', thresh[:, final[index]-1:cut])       
            
    # Show for visualization
    #plt.imshow(thresh[:, final[0]:] , cmap='gray')


def getFinalCut(index, img, thresh):
    (h,w) = thresh.shape
    found = True
    # Count of how many black should exist in a single column 
    black_pixel_count_threshold = 2
    # Count of black pixels that should be in series
    black_pixel_occurance_threshold = 2

    # Save all the column indexes for cutting later
    black_cut = []
    for col in range(w):
        found = True
        # Get the count of zeros from the column
        white_count = thresh[:baseline, col].shape[0]- np.count_nonzero(thresh[:baseline, col])
        # Checker whether the black count is less than the threshold, if more it might not be a perfect cut
        if white_count <= black_pixel_count_threshold:
            # Get the last (black_pixel_occurance_threshold) values from the column
            for black in thresh[:baseline, col][thresh[:baseline, col].shape[0]-black_pixel_occurance_threshold:]:
                # Check whether if all black pixels are in series or no, if yes then make found True
                if black != 0:
                    found = False
            # If black pixels were found in series then append the column index
            if found:
                if not col >= (w - 5):
                    black_cut.append(col)
        

    # Remove column indexes that are in series by adjusting the increment value, and remove duplicates
    increment = 2
    to_remove = set()
    for x in black_cut:
        if x not in to_remove:
            for i in range(1, 1 + increment):
                to_remove.add(x - i)
                to_remove.add(x + i)
                
    final = [x for x in black_cut if x not in to_remove]
    for cut in final:
        cv2.line(img, (cut, 0), (cut,h), (0,255,0), 1)
    cv2.imwrite(f'{index}_split.jpg', img)

    return final


def splitAllChars(thresh, blocks):
    index = 0
    for final in tqdm(blocks):
        for count, cut in enumerate(final):
            if index == 0 and len(final) > 1:
                cv2.imwrite(f'final_char/{index}.jpg', thresh[:, 0:cut])
                
            # If only one cut is found split the image in 2 halves and save them both
            elif index == 0 and len(final) == 1:
                cv2.imwrite(f'final_char/{index}.jpg', thresh[:, 0:cut])
                cv2.imwrite(f'final_char/{index+1}.jpg', thresh[:, cut:])
                
            elif index == len(final)-1:
                cv2.imwrite(f'final_char/{index}.jpg', thresh[:, final[index-1]:cut])
                cv2.imwrite(f'final_char/{index+1}.jpg', thresh[:, cut:])
            else:
                cv2.imwrite(f'final_char/{index}.jpg', thresh[:, final[index-1]:cut])     
            index+=1

print('Delete folder contents...')
time.sleep(0.3)
folders = ['chars/', 'final_char']
for folder in tqdm(folders):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='path to the word image file')
    args = parser.parse_args()

    img = cv2.imread(args.path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)  

    print("Finding baseline....")
    count, baseline = findBaseLine(img, thresh)
    print(f"Baseline is: {baseline}")

    print()
    print("Splitted images saved in chars/")
    splitWhiteSpaces(thresh)


    splittedImages = os.listdir('chars/')
    blocks = []

    print()
    print("Splitted all characters....")
    time.sleep(0.3)
    index = 0
    for image in tqdm(splittedImages):
        img = cv2.imread(f'chars/{image}')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY) 

        final = getFinalCut(index, img, thresh)
        blocks.append(final) 
        index+=1

    print()
    print("Saving characters...")
    splitAllChars(thresh, blocks)