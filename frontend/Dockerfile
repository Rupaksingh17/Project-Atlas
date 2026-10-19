FROM php:8.4-apache

RUN apt-get update && apt-get install -y --no-install-recommends libcurl4-openssl-dev \
    && docker-php-ext-install curl mysqli pdo pdo_mysql \
    && a2enmod rewrite headers \
    && rm -rf /var/lib/apt/lists/*

COPY apache-security-headers.conf /etc/apache2/conf-available/atlas-security-headers.conf
RUN a2enconf atlas-security-headers

# Copy self-contained CodeIgniter 3 application
COPY . /var/www/html/

# Ensure Apache web server permissions
RUN mkdir -p /var/www/html/application/logs /var/www/html/application/cache/sessions \
    && chown -R www-data:www-data /var/www/html

EXPOSE 80
