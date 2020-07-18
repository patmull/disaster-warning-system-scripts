import os
import smtplib

#EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
#EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', None)
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', None)


def send_error_email(error_text):

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        subject = 'URGENT!!! ERROR OCCURED IN PYTHON SCRIPT!!!'
        body = 'There was an error in Python script. Please respond immiidately.'

        message = 'Subject: ' + subject + '\n\n' + body + '\n\n ERROR TYPE: ' + error_text

        smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)

