import pyotp
print(pyotp.TOTP('your_secret_key').now())  #Enter the MFA Setup Endpoint's secret