DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS service_definitions;
DROP TABLE IF EXISTS service_access;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS titles;
DROP VIEW IF EXISTS all_services;

CREATE TABLE services (
  name VARCHAR(32) PRIMARY KEY,
  sso BOOLEAN NOT NULL DEFAULT (CAST (0 AS BOOLEAN))
);

CREATE TABLE service_definitions (
  service VARCHAR(32),
  language CHAR(2) NOT NULL,
  title VARCHAR(128),
  description TEXT,
  FOREIGN KEY (service) REFERENCES services(name)
);

CREATE TABLE categories (
  name VARCHAR(16) PRIMARY KEY,
  ordr INTEGER
);

CREATE TABLE service_access (
  service VARCHAR(32) NOT NULL,
  category VARCHAR(16) NOT NULL,
  url VARCHAR(128) NOT NULL,
  access VARCHAR(128),
  icon_url VARCHAR(128),
  FOREIGN KEY (service) REFERENCES services(name),
  FOREIGN KEY (category) REFERENCES categories(name)
);

CREATE TABLE titles (
  name VARCHAR(16) NOT NULL,
  language CHAR(2) NOT NULL,
  title TEXT NOT NULL,
  CONSTRAINT name_lang UNIQUE (name, language)
);

CREATE VIEW all_services (
  category_name, category, service, title, description, access, url, icon_url,
  sso, language
) AS
SELECT      c.name, t.title, s.name, sd.title, sd.description, sa.access,
            sa.url, sa.icon_url, s.sso, sd.language
  FROM      services s
  JOIN      service_definitions sd ON s.name = sd.service
  JOIN      service_access sa ON sd.service = sa.service
  JOIN      categories c ON sa.category = c.name
  JOIN      titles t ON c.name = t.name
  WHERE     sd.language = t.language
  ORDER BY  c.ordr
;
