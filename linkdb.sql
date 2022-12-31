SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `backlinks` (
  `id` int NOT NULL,
  `subdomain_to` int NOT NULL,
  `subdomain_from` int NOT NULL,
  `url_to` text NOT NULL,
  `url_from` text NOT NULL,
  `to_page_id` int NOT NULL,
  `from_page_id` int NOT NULL,
  `composite_md5` char(32) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pages` (
  `id` int NOT NULL,
  `subdomain_id` int NOT NULL,
  `url` text NOT NULL,
  `contents_md5` char(32) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `sitelabels` (
  `id` int NOT NULL,
  `domain_label` varchar(63) NOT NULL,
  `first_crawled` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `subdomains` (
  `id` int NOT NULL,
  `label_id` int NOT NULL,
  `domain` varchar(253) NOT NULL DEFAULT '#',
  `first_crawled` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


ALTER TABLE `backlinks`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `composite_md5` (`composite_md5`),
  ADD KEY `subdomain_to_from` (`subdomain_to`,`subdomain_from`),
  ADD KEY `from_page_id` (`from_page_id`),
  ADD KEY `to_page_id` (`to_page_id`);

ALTER TABLE `pages`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `contents_md5` (`contents_md5`),
  ADD KEY `subdomain` (`subdomain_id`);

ALTER TABLE `sitelabels`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `domain_label` (`domain_label`);

ALTER TABLE `subdomains`
  ADD PRIMARY KEY (`id`),
  ADD KEY `label` (`label_id`);


ALTER TABLE `backlinks`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `pages`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `sitelabels`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `subdomains`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
