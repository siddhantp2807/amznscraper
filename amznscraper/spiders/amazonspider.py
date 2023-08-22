import scrapy, random, time, re
from amznscraper.items import AmazonItem


class AmazonSpider(scrapy.Spider) :

    name = "amazon"

    start_urls = [
        "https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_1"
    ]

    def start_requests(self) :

        for url in self.start_urls :
            self.random_delay()
            yield scrapy.Request(url, headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"}, callback=self.parse)
    
    def parse(self, response) :

        products = response.css("div[data-asin]")
        for product in products :

            item = AmazonItem()
            float_pattern = r'[-+]?\d*\.\d+|\d+'
            
            if product.attrib['data-asin'] != '' :
                item['name'] = product.css('h2').xpath('.//text()').get()
                item['url'] = f'https://amazon.in/dp/{product.attrib["data-asin"]}'
                
                if product.css("span.a-price-whole::text").get() is not None :
                    item['price'] = product.css("span.a-price-whole::text").get().replace(",", "")
                else :
                    item['price'] = 'N/A'
                
                rating = product.css("span[aria-label]").xpath(".//text()").get()
                if rating is not None :
                    found = re.findall(float_pattern, rating)
                    if found != [] :
                        item['rating'] = found[0]
                    else :
                        item['rating'] = "N/A"
                else :
                    item['rating'] = "N/A"
                
                item['no_of_reviews'] = product.css("span.s-underline-text::text").get()
                item['asin'] = product.attrib['data-asin']

                # yield item
                yield scrapy.Request(item['url'], headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"}, callback=self.parse_product, meta={'item' : item})

        if response.css("a.s-pagination-next") != [] :
            next_url = response.css("a.s-pagination-next").attrib["href"]
            full_url = f'https://www.amazon.in{next_url}'
            self.random_delay()
            yield scrapy.Request(full_url, headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"}, callback=self.parse)

    def parse_product(self, response) :

        item = response.meta['item']
        descs = response.css("div#productDescription").xpath(".//text()").getall()
        item['description'] = "".join(descs).strip()

        bullets = response.css("div#detailBullets_feature_div")
        properties = bullets.css("span.a-list-item")

        for prop in properties :
            
            txt = prop.xpath(".//text()").getall()
            fulltxt = "".join(txt)
            
            if "Manufacturer" in fulltxt :
                cleaned_string = re.sub(r'[^a-zA-Z0-9\s:.,-]', '', fulltxt)
                item["manufacturer"] = cleaned_string.split("Manufacturer")[1].strip()[1:].strip()
                break
        
        yield item

    def random_delay(self) :
        delay = random.uniform(1, 5)
        time.sleep(delay)