# -*- coding: utf-8 -*-
"""
Created on Thu May 30 12:52:09 2024

@author: Francisco
"""

import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.image as mpimg
from scipy.stats import linregress
from scipy import stats
from scipy.optimize import curve_fit

SQUARE_SIZE=60
X_OFFSET=10
Y_OFFSET=45
BARNEY_PARAMETERS=[]

def fit_linear_regression(ppm_values, dye_values,i):
    """
    Fits a linear regression model to dye calibration values.
    :param ppm_values: Known PPM values.
    :param dye_values: Calibration values for a dye.
    :return: Slope and intercept of the fitted line.
    """
    slope, intercept, _, _, _ = linregress(ppm_values, dye_values)
    predicted_pixels = intercept + slope * np.array(ppm_values)
    residuals = np.array(dye_values) - predicted_pixels

    sigma = np.std(residuals, ddof=1)
    LDL = 3.3*sigma/slope
    print("Dye ",i+1)
    print("Slope: ", slope)
    print("Standar deviation of residuals: ", sigma)
    print("Limit of detection (LDL): ",abs(LDL))


    return slope, intercept

def predict_ppm_from_sample(slope, intercept, sample_value,dye):
    """
    Uses the linear regression line to predict PPM for a given sample pixel value and to keep the predicted PPM between 0 and 10.
    Aditionally, the PPM is set to 0 when sample_value is greater than 238 when a dye is measured by utilising gray scale.
    :param slope: Slope of the dye's regression line.
    :param intercept: Intercept of the dye's regression line.
    :param sample_value: The pixel value to predict PPM for.
    :return: Predicted PPM.
    """
    ppm=(sample_value - intercept) / slope
    print(sample_value)
    if dye == 5 or dye == 6:
        if sample_value[0] > 238:
            ppm[0]=0.0
    if ppm[0]<0:
        ppm[0]=0
    if ppm[0]>10:
        ppm[0]=10

    return ppm

def plot_with_regression_and_images(calibration_images, sample_images):
    # Define PPM values and prepare colors for each dye
    dye1,dye2,dye3,dye4,dye5,dye6=colorimetry()
    s1,s2,s3,s4,s5,s6=colorimetry_samples()
    samples=[s1,s2,s3,s4,s5,s6]
    ppm_values = [ 2, 4, 6, 8, 10]
    dyes = [dye1, dye2, dye3, dye4, dye5, dye6]
    colors = ["lightgoldenrodyellow", "sandybrown", "yellow", "purple", "lightcoral", "gold"]
    sample_labels = ['s1', 's2', 's3', 's4', 's5', 's6']

    # Create a figure with gridspec to organize the layout
    fig = plt.figure(figsize=(10, 18), facecolor='black')
    gs = gridspec.GridSpec(nrows=8, ncols=6, height_ratios=[3, 2, 1, 1, 1, 1, 1, 1], width_ratios=[1, 1, 1, 1, 1, 1])

    # Create the regression plot space
    ax_reg = fig.add_subplot(gs[0, :])  # Regression plot spans all columns
    ax_reg.set_facecolor('black')
    ax_reg.tick_params(colors='white')
    ax_reg.spines['bottom'].set_color('white')
    ax_reg.spines['left'].set_color('white')
    ax_reg.xaxis.label.set_color('white')
    ax_reg.yaxis.label.set_color('white')
    ax_reg.title.set_color('white')
    ax_reg.set_xlim(0, 10)
    ax_reg.set_ylim(0, 300)

    # Store slopes and intercepts
    slopes_intercepts = []

    # Plot regression lines for each dye
    for i, dye_values in enumerate(dyes):
        if i+1==4:
            # Plot the regression line
            A,B,C,D = BARNEY_PARAMETERS[0]
            aprox_line_x = np.arange(0, 10, 0.1)
            aprox_line_y = A/(B+(C*aprox_line_x+D)**3)
            plt.plot(aprox_line_x, aprox_line_y, linestyle='--', color="purple", label=f"Dye {i+1}", alpha=0.6)
            slopes_intercepts.append((0.0, 0.0))
        else:
            # Perform linear regression
            slope, intercept = fit_linear_regression(ppm_values, dye_values,i)
            slopes_intercepts.append((slope, intercept))

            # Plot the regression line
            reg_line_x = np.array([0] + ppm_values)
            reg_line_y = slope * reg_line_x + intercept
            ax_reg.plot(reg_line_x, reg_line_y, linestyle='--', color=colors[i], label=f"Dye {i+1}", alpha=0.6)

    # Predict and plot each sample
    predicted_ppm_values = []
    for i, (sample_value, (slope, intercept), label) in enumerate(zip(samples, slopes_intercepts, sample_labels)):
        # Predict ppm for each sample
        if i+1 == 4:
            predicted_ppm = barney_curve_predict_value(sample_value, A, B, C, D)
        else:
            predicted_ppm = predict_ppm_from_sample(slope, intercept, sample_value, i+1)
        predicted_ppm_values.append((f"Dye {i+1}", predicted_ppm))

        # Plot the sample points
        if not np.isnan(predicted_ppm):
            ax_reg.scatter(predicted_ppm, sample_value, marker='x', color=colors[i])

    # Classify as porous or non-porous
    porous_count = sum(1 for _, ppm in predicted_ppm_values if ppm < 0.2)
    material_type = "Porous" if porous_count > 1 else "Non-Porous"
    print("The material is: ",material_type)

    # Display predictions and classification
    text_str = "Predicted PPMs:\n" + "\n".join(f"{dye}: {ppm[0]:.2f}" for dye, ppm in predicted_ppm_values)
    text_str += f"\n\nClassification: {material_type}"
    plt.text(1.05, 0.5, text_str, transform=ax_reg.transAxes, fontsize=12, color='white', va='center')
    
    # Final plot settings
    ax_reg.set_xlabel("PPM")
    ax_reg.set_ylabel(f"Pixel Value - (0-256)")
    material_name=MATERIAL_NAME
    ax_reg.set_title(f"Predicted PPMs for {material_name}")
    ax_reg.legend(facecolor='black', edgecolor='white', labelcolor='white')

    # Create a grid of images below the regression plot
    num_dyes = len(calibration_images)  # Each dye has its own column
    num_rows = len(ppm_values)  # No need for additional row for samples as they are in the first row

    # Plot sample images in the first row of the grid
    for col, img_path in enumerate(sample_images):
        if col < num_dyes:
            image = mpimg.imread(img_path)
            ax_img = fig.add_subplot(gs[1, col])  # Place sample images in the first row
            ax_img.imshow(image)
            ax_img.axis('off')
            ax_img.set_title(f"Dye {col+1}", color="white")

    # Plot calibration images for each dye
    for col, dye_images in enumerate(calibration_images):
        for row, ppm_value in enumerate(ppm_values):
            if row < len(dye_images):
                image = mpimg.imread(dye_images[row])
                ax_img = fig.add_subplot(gs[row + 2, col])  # Start from the second row for PPM images
                ax_img.imshow(image)
                ax_img.axis('off')
                if col == 0:  # Label only the first column for ppm values
                    ax_img.set_ylabel(f"{ppm_value} PPM", color="white", rotation=0, labelpad=10)

    # Adjust layout to avoid overlap
    plt.tight_layout()
    plt.savefig(RESULTS_PATH+MATERIAL_NAME+'_RESULTS.jpg',dpi = 400)
    plt.show()
    


def draw_center_square_mode(image_path, output_path, square_size=SQUARE_SIZE, channel='gray'):
    """
    Draws a square in the center of the image and calculates the mode pixel value for the selected channel.
    
    :param image_path: Path to the input image
    :param output_path: Path to save the modified image
    :param square_size: Size of the square region to analyze
    :param channel: Channel to select for mode calculation ('gray', 'R', 'G', 'B')
    :return: Mode value of the selected channel
    """
    # Read the image
    image = cv2.imread(image_path)
    
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Split the image into B, G, R channels
    B_channel, G_channel, R_channel = cv2.split(image)
    
    # Get image dimensions
    height, width = gray_image.shape
    
    # Calculate the center of the image
    center_x, center_y = width // 2, height // 2
    
    # Adjust center for the liquid position if needed
    center_x += X_OFFSET  
    center_y += Y_OFFSET  
    
    # Calculate the top-left and bottom-right corners of the square
    top_left_x = center_x - (square_size // 2)
    top_left_y = center_y - (square_size // 2)
    bottom_right_x = center_x + (square_size // 2)
    bottom_right_y = center_y + (square_size // 2)
    
    # Extract the square region for each channel
    square_gray = gray_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_B = B_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_G = G_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_R = R_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    
    # Calculate the mode for each channel
    mode_gray = stats.mode(square_gray, axis=None)[0][0]
    mode_B = stats.mode(square_B, axis=None)[0][0]
    mode_G = stats.mode(square_G, axis=None)[0][0]
    mode_R = stats.mode(square_R, axis=None)[0][0]
    
    # Choose the correct mode value based on the selected channel
    if channel == 'gray':
        mode_value = mode_gray
        cv2.rectangle(gray_image, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        cv2.imwrite(output_path, gray_image)
    elif channel == 'B':
        mode_value = mode_B
        cv2.rectangle(B_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    elif channel == 'G':
        mode_value = mode_G
        cv2.rectangle(G_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    elif channel == 'R':
        mode_value = mode_R
        cv2.rectangle(R_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    else:
        raise ValueError("Invalid channel selection. Choose from 'gray', 'B', 'G', 'R'.")
    
    return mode_value

def draw_center_square_mean(image_path, output_path, square_size=SQUARE_SIZE, channel='gray'):
    """
    Draws a square in the center of the image and calculates the mean (average) pixel value for the selected channel.
    
    :param image_path: Path to the input image
    :param output_path: Path to save the modified image
    :param square_size: Size of the square region to analyze
    :param channel: Channel to select for mean calculation ('gray', 'R', 'G', 'B')
    :return: Mean value of the selected channel
    """
    # Read the image
    image = cv2.imread(image_path)
    
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Split the image into B, G, R channels
    B_channel, G_channel, R_channel = cv2.split(image)
    
    # Get image dimensions
    height, width = gray_image.shape
    
    # Calculate the center of the image
    center_x, center_y = width // 2, height // 2
    
    # Adjust center for the liquid position if needed
    center_x += X_OFFSET  # Adjust as necessary
    center_y += Y_OFFSET  # Adjust as necessary
    
    # Calculate the top-left and bottom-right corners of the square
    top_left_x = center_x - (square_size // 2)
    top_left_y = center_y - (square_size // 2)
    bottom_right_x = center_x + (square_size // 2)
    bottom_right_y = center_y + (square_size // 2)
    
    # Extract the square region for each channel
    square_gray = gray_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_B = B_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_G = G_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_R = R_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    
    # Calculate the mean (average) for each channel
    mean_gray = np.mean(square_gray)
    mean_B = np.mean(square_B)
    mean_G = np.mean(square_G)
    mean_R = np.mean(square_R)
    
    # Choose the correct mean value based on the selected channel
    if channel == 'gray':
        mean_value = mean_gray
        cv2.rectangle(gray_image, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        cv2.imwrite(output_path, gray_image)
    elif channel == 'B':
        mean_value = mean_B
        cv2.rectangle(B_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    elif channel == 'G':
        mean_value = mean_G
        cv2.rectangle(G_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    elif channel == 'R':
        mean_value = mean_R
        cv2.rectangle(R_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        cv2.imwrite(output_path, modified_image)
    else:
        raise ValueError("Invalid channel selection. Choose from 'gray', 'B', 'G', 'R'.")
    
    return mean_value


def draw_center_square(image_path, output_path, square_size=SQUARE_SIZE, channel='B'):
    """
    Draws a square in the center of the image and calculates the median pixel value for the selected channel.
    
    :param image_path: Path to the input image
    :param output_path: Path to save the modified image
    :param square_size: Size of the square region to analyze
    :param channel: Channel to select for median calculation ('gray', 'R', 'G', 'B')
    :return: Median value of the selected channel
    """
    # Read the image
    image = cv2.imread(image_path)

    # Convert BGR to HSV and parse HSV
    hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    H_channel, S_channel, V_channel = hsv_img[:, :, 0], hsv_img[:, :, 1], hsv_img[:, :, 2]


    # Convert BGR to LAB and parse LAB
    lab_img = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    L_channel, A_channel, BB_channel = lab_img[:, :, 0], lab_img[:, :, 1], lab_img[:, :, 2]
    
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization to grayscale
    equalized_gray_image = cv2.equalizeHist(gray_image)
    
    # Split the image into B, G, R channels
    B_channel, G_channel, R_channel = cv2.split(image)
    
    # Get image dimensions
    height, width = equalized_gray_image.shape
    
    # Calculate the center of the image
    center_x, center_y = width // 2, height // 2
    
    # Adjust center for the liquid position if needed
    center_x += X_OFFSET  # Adjust as necessary
    center_y += Y_OFFSET  # Adjust as necessary
    
    # Calculate the top-left and bottom-right corners of the square
    top_left_x = center_x - (square_size // 2)
    top_left_y = center_y - (square_size // 2)
    bottom_right_x = center_x + (square_size // 2)
    bottom_right_y = center_y + (square_size // 2)
    
    # Extract the square region for each channel
    square_gray = equalized_gray_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_B = B_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_G = G_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_R = R_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_H = H_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_S = S_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_V = V_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_L = L_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_A = A_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    square_BB = BB_channel[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    
    # Calculate the median for each channel
    median_gray = np.median(square_gray)
    median_B = np.median(square_B)
    median_G = np.median(square_G)
    median_R = np.median(square_R)
    median_H = np.median(square_H)
    median_S = np.median(square_S)
    median_V = np.median(square_V)
    median_L = np.median(square_L)
    median_A = np.median(square_A)
    median_BB = np.median(square_BB)
    
    # Choose the correct median value based on the selected channel
    if channel == 'gray':
        median_value = median_gray
        # Draw a white square on the grayscale image
        cv2.rectangle(equalized_gray_image, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified grayscale image
        cv2.imwrite(output_path, equalized_gray_image)
    elif channel == 'B':
        median_value = median_B
        # Draw a square on the Blue channel
        cv2.rectangle(B_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Merge back the B channel into the original image
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        # Save the modified image
        cv2.imwrite(output_path, modified_image)
    elif channel == 'G':
        median_value = median_G
        # Draw a square on the Green channel
        cv2.rectangle(G_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Merge back the G channel into the original image
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        # Save the modified image
        cv2.imwrite(output_path, modified_image)
    elif channel == 'R':
        median_value = median_R
        # Draw a square on the Red channel
        cv2.rectangle(R_channel, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Merge back the R channel into the original image
        modified_image = cv2.merge([B_channel, G_channel, R_channel])
        # Save the modified image
        cv2.imwrite(output_path, modified_image)
    elif channel == 'H':
        median_value = median_H
        # Draw a square on the H channel
        cv2.rectangle(hsv_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, hsv_img)
    elif channel == 'S':
        median_value = median_S
        # Draw a square on the S channel
        cv2.rectangle(hsv_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, hsv_img)
    elif channel == 'V':
        median_value = median_V
        # Draw a square on the V channel
        cv2.rectangle(hsv_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, hsv_img)
    elif channel == 'L':
        median_value = median_L
        # Draw a square on the L channel
        cv2.rectangle(lab_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, lab_img)
    elif channel == 'A':
        median_value = median_A
        # Draw a square on the A channel
        cv2.rectangle(lab_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, lab_img)
    elif channel == 'BB':
        median_value = median_BB
        # Draw a square on the B (lab) channel
        cv2.rectangle(lab_img, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (255), 2)
        # Save the modified image
        cv2.imwrite(output_path, lab_img)
    

    else:
        raise ValueError("Invalid channel selection. Choose from 'gray', 'B', 'G', 'R'.")
    return median_value

def colorimetry():
    dye1=[]
    dye2=[]
    dye3=[]
    dye4=[198]
    dye5=[]
    dye6=[]
    for i in [2,4,6,8,10]:
        average_value = draw_center_square(DYE1_PATH+"dye1_"+str(i)+'ppm.jpg', DYE1_PATH+'ROI_calibration_dye1_'+str(i)+'_ppm.jpg',channel='S')
        dye1.append(average_value)
        average_value = draw_center_square(DYE2_PATH+"dye2_"+str(i)+'ppm.jpg', DYE2_PATH+'ROI_calibration_dye2'+str(i)+'_ppm.jpg',channel='BB')
        dye2.append(average_value)
        average_value = draw_center_square(DYE3_PATH+"dye3_"+str(i)+'ppm.jpg', DYE3_PATH+'ROI_calibration_dye3'+str(i)+'_ppm.jpg',channel='gray')
        dye3.append(average_value)
        average_value = draw_center_square(DYE4_PATH+"dye4_"+str(i)+'ppm.jpg', DYE4_PATH+'ROI_calibration_dye4'+str(i)+'_ppm.jpg',channel='L')
        dye4.append(average_value)
        average_value = draw_center_square(DYE5_PATH+"dye5_"+str(i)+'ppm.jpg', DYE5_PATH+'ROI_calibration_dye5'+str(i)+'_ppm.jpg',channel='gray')
        dye5.append(average_value)
        average_value = draw_center_square(DYE6_PATH+"dye6_"+str(i)+'ppm.jpg', DYE6_PATH+'ROI_calibration_dye6'+str(i)+'_ppm.jpg',channel='gray')
        dye6.append(average_value)
        print(dye4)
    #plot_colorimetry_calibration([2,4,6,8,10],dye1,"Dye 1")
    #plot_colorimetry_calibration([2,4,6,8,10],dye2,"Dye 1")
    #plot_colorimetry_calibration([2,4,6,8,10],dye3,"Dye 1")
    plot_colorimetry_calibration([0,2,4,6,8,10],dye4,"Dye 4")
    #input()
    #plot_colorimetry_calibration([2,4,6,8,10],dye5,"Dye 1")
    #plot_colorimetry_calibration([2,4,6,8,10],dye6,"Dye 1")
    dye4.pop()
    return dye1,dye2,dye3,dye4,dye5,dye6

def plot_colorimetry_calibration(ppm,pixels,title):
    #plt.plot(ppm, pixels, 'o')
    # Parameters
    #curve_parameters = []

    # Plot regression lines for each dye
    # Perform curve fit
    guess = (245, 240, 1.5, 1.1)

    f_prof, f_err = curve_fit(barney_curve, ppm, pixels, guess)
    A,B,C,D = f_prof
    BARNEY_PARAMETERS.append((A, B, C, D))
    #curve_parameters.append((A,B,C,D))

    # Plot the regression line
    #aprox_line_x = np.arange(0, 10, 0.1)
    #aprox_line_y = A/(B+(C*aprox_line_x+D)**3)
    #predicted_ppm = barney_curve_predict_value(pixels, A, B, C, D)
    #print(predicted_ppm)
    #input()
    #exit()
    #plt.plot(aprox_line_x, aprox_line_y, linestyle='--', color="purple", label=title+ " predicted curve", alpha=0.6)
    #plt.title(title)
    #plt.xlabel("PPMs")
    #plt.ylabel("Pixels")
    #plt.show()

def barney_curve(x,A,B,C,D):
    return A/(B+(C*np.array(x)+D)**3)

def barney_curve_predict_value(pixels,A,B,C,D):
    ppm = (np.cbrt((A/pixels)- B)-D)/C
    if ppm[0]<0:
        ppm[0]=0
    if ppm[0]>10:
        ppm[0]=10
    return ppm

def colorimetry_samples():
    dye1=[]
    dye2=[]
    dye3=[]
    dye4=[]
    dye5=[]
    dye6=[]
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE1.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE1.jpg',channel='S')
    dye1.append(average_value)
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE2.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE2.jpg',channel='BB')
    dye2.append(average_value)
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE3.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE3.jpg',channel='gray')
    dye3.append(average_value)
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE4.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE4.jpg',channel='L')
    dye4.append(average_value)
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE5.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE5.jpg',channel='gray')
    dye5.append(average_value)
    average_value = draw_center_square(SAMPLES_PATH+MATERIAL_NAME+"_DYE6.jpg", OUTPUT_PATH+'ROI_SAMPLE_DYE6.jpg',channel='gray')
    dye6.append(average_value)
    print(dye1,dye2,dye3,dye4,dye5,dye6)
    return dye1,dye2,dye3,dye4,dye5,dye6

if __name__=='__main__':
    #C:\Users\Francisco\OneDrive - Cardiff University\Desktop\robinhood_imgs\TEMP\results\CMP2_a
    #C:\Users\Francisco\OneDrive - Cardiff University\Desktop\robinhood_imgs\imgs\
    #Tha bash script has to add SAMPLES_PATH and OUTPUT_PATH automatically
    #CALIBRATION_PATH should be already there at the level of the bash script.
    try:
        MATERIAL_NAME=sys.argv[1]
        GLOBAL_PATH=sys.argv[2]
    except:
        MATERIAL_NAME='CMP2_a'
        GLOBAL_PATH=''
    CALIBRATION_PATH=GLOBAL_PATH+'imgs/calibration_imgs/'
    DYE1_PATH=CALIBRATION_PATH+'dye1/'
    DYE2_PATH=CALIBRATION_PATH+'dye2/'
    DYE3_PATH=CALIBRATION_PATH+'dye3/'
    DYE4_PATH=CALIBRATION_PATH+'dye4/'
    DYE5_PATH=CALIBRATION_PATH+'dye5/'
    DYE6_PATH=CALIBRATION_PATH+'dye6/'
    SAMPLES_PATH=GLOBAL_PATH+'TEMP/'+MATERIAL_NAME+'/imgs/'
    OUTPUT_PATH=GLOBAL_PATH+'TEMP/'+MATERIAL_NAME+'/ROI_output/'
    RESULTS_PATH=GLOBAL_PATH+'TEMP/'+MATERIAL_NAME+'/'
    ##################################################################
    calibration_images = [
        [DYE1_PATH + f"dye1_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
        [DYE2_PATH + f"dye2_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
        [DYE3_PATH + f"dye3_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
        [DYE4_PATH + f"dye4_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
        [DYE5_PATH + f"dye5_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
        [DYE6_PATH + f"dye6_{ppm}ppm.jpg" for ppm in [2, 4, 6, 8, 10]],
    ]
    sample_images = [
        SAMPLES_PATH + MATERIAL_NAME+"_DYE1.jpg",
        SAMPLES_PATH + MATERIAL_NAME+"_DYE2.jpg",
        SAMPLES_PATH + MATERIAL_NAME+"_DYE3.jpg",
        SAMPLES_PATH + MATERIAL_NAME+"_DYE4.jpg",
        SAMPLES_PATH + MATERIAL_NAME+"_DYE5.jpg",
        SAMPLES_PATH + MATERIAL_NAME+"_DYE6.jpg",
    ]
    print(MATERIAL_NAME)
    print(GLOBAL_PATH)
    print(CALIBRATION_PATH)
    print(SAMPLES_PATH)
    print(OUTPUT_PATH)
    print(DYE1_PATH)

    print(sys.argv[1])
    print(sys.argv[2])

    print(sample_images)
    plot_with_regression_and_images(calibration_images, sample_images)

