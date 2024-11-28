This is an ecommerce website made with Django and Bootstrap/Javascript

# FEATURES:
- Postgresql Database, you can create your desired database and configure it on the settings.py or uncomment the sqlite part and comment 
 on the postgresql part to use sqlite. 
- Full-featured shopping cart
- Review and Rating System
- Product pagination
- Product search feature
- User profile with orders
- Admin area to manage customers, products & orders
- Mark orders as a delivered option
- Checkout process (shipping, payment method, etc... )
- Category Filter
- Addition of variable products
- About us page   
- Contact page
- An unlimited number of products and categories
- Unlimited pages 
- Products are uploaded via the admin panel and the photos saved in the 'media' folder


HOW TO RUN THIS PROJECT
- Install Python
- Create a virtual environment
- Download This Project Zip Folder and Extract it inside the virtual environment or alternatively, you can clone it and save it on your computer
- Open Terminal and Execute Following Commands :

``` python -m pip install -r requirements.txt ``` 
- Move to project folder in the Terminal. Then run following Commands :
```
py manage.py makemigrations
py manage.py migrate
py manage.py runserver
```

Open your browser and launch it on http://127.0.0.1:8000/

REQUIRED CHANGES FOR THE CONTACT US PAGE:
- In settings.py file, You have to give your email and password. Go to your email settings and generate the app password which you will use on the EMAIL_HOST_PASSWORD line.

```
EMAIL_HOST_USER = 'youremail@gmail.com'
EMAIL_HOST_PASSWORD = 'your email password'
EMAIL_RECEIVING_USER = 'youremail@gmail.com'
```



NAVIGATE TO THE 'SCREENSHOTS' FOLDER TO VIEW SCREENSHOTS OF THE PROJECT


