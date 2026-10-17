FROM php:8.1-apache

RUN docker-php-ext-install mysqli pdo pdo_mysql
RUN a2enmod rewrite

# Copy self-contained CodeIgniter 3 application
COPY . /var/www/html/

# Ensure Apache web server permissions
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80
