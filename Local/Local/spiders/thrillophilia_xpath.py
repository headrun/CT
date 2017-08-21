top_page_xpath = '//a[contains(@href,"/listings?search")]/@href'

activities_links_xpath = '//div[@class="name"]/a[contains(@href,"/tours/")]/@href'

load_more_collection_link_xpath = '//a[contains(@href,"load_more=true&page=")]/@href'

title_xpath = '//div[@class="banner_section visible-xs"]//h1[@class="tour_title bold_text"]/text()'

location_xpath = '//div[@class="banner_section"]//div[@class="specs"]/span[@class="icon"][text()="l"]/following-sibling::span[@class="text"]/text()'

rating_xpath = '//div[@class="banner_section visible-xs"]//span[@class="rating_count"]/text()'

price_xpath = '//div[@class="banner_section"]//span[@class="final_price hidden-xs"]/span[@class="amount"]/text()'

no_of_days_nights_xpath = '//div[@class="banner_section"]//div[@class="specs"]/span[@class="icon"][text()="l"]/preceding-sibling::span[@class="text"]/text()'

cashback_xpath = '//div[@class="banner_section"]//span[@class="tour_cashback"]/text()'

special_offer_xpath = '//div[@class="banner_section"]//span[@class="discount_amount hidden-xs"]/text()'

overview_xpath = '//div[@class="overview_details"]//text()'

itinerary_xpath = '//ul[@class="itinerary_list"]//text()'

stay_xpath = '//h3[contains(text(),"Stay")]/..//li/text()'

meal_xpath = '//h3[contains(text(),"Meal")]/../ul[@class="option_one"]//li/text()'

activity_xpath = '//h3[contains(text(),"Activity")]/../ul[@class="option_one"]//li/text()'

things_to_carry_xpath = '//h3[contains(text(),"Things To Carry")]/../ul[@class="option_one"]//li/text()'

advisory_xpath = '//h3[contains(text(),"Advisory")]/../ul[@class="option_one"]//li/text()'

tour_type_xpath = '//h3[contains(text(),"Tour Type")]/../ul[@class="option_one"]//li/text()'

other_inclusions_xpath = '//h3[contains(text(),"Other Inclusions")]/../ul[@class="option_one"]//li/text()'

cancellation_policy_xpath = '//h3[contains(text(),"Cancellation Policy")]/../ul[@class="option_one"]//li/text()'

refund_policy_xpath = '//h3[contains(text(),"Refund Policy")]/../ul[@class="option_one"]//li/text()'

confirmation_policy_xpath = '//h3[contains(text(),"Confirmation Policy")]/../ul[@class="option_one"]//li/text()'

images_xpath = '//div[@class="banner_section"]//a[contains(@href,"/image/upload/s")]/@href'

reviews_page_xpath = '//div[@class="view_all_button_wrapper"]/a/@href'

reviews_count_xpath = '//div[@class="banner_section"]//a[contains(@href,"#stories")]/span/text()'
