FROM php:7.4-apache

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tar \
    && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-install mysqli pdo pdo_mysql
RUN a2enmod rewrite

# Download CodeIgniter 3.1.13 framework core
ADD https://github.com/bcit-ci/CodeIgniter/archive/refs/tags/3.1.13.tar.gz /tmp/ci.tar.gz
RUN tar -xzf /tmp/ci.tar.gz -C /var/www/html --strip-components=1 && rm /tmp/ci.tar.gz

# Overlay our application directory
COPY ./application /var/www/html/application

# Ensure correct permissions
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80
