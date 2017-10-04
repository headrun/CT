economy_price_key_value_xpath = '//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@value'

economy_price_key_name_xpath = '//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoSmart"]/div[@class="fare-price-text  no-bundle"]/input/@name'

oneway_additional_key_xpath = '//div[@id="js_availability_container"]/form/input/@name'

oneway_additional_value_xpath = '//div[@id="js_availability_container"]/form/input/@value'

business_price_key_value_xpath = '//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@value'

business_price_key_name_xpath = '//div[contains(text(),"%s")]/../../td[@data-mobile-label="GoBusiness"]/div[@class="fare-price-text  no-bundle"]/input/@name'

roundtrip_additional_keys_xpath = '//form[@id="availabilityForm"]/input[@type="hidden"]/@name'

error_text_xpath = '//h4[@class="alert-heading"][contains(text(),"Errors")]/../ul/li/text()'

oneway_addon_value_xpath = '//span[contains(text(),"%s")]/../..//div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone"]//option[contains(text()," %s ")]/@value'

rountrip_addon_value_xpath = '//span[contains(text(),"%s")]/../../div[@class="mdl-cell mdl-cell--12-col mdl-cell--8-col-tablet mdl-cell--12-col-phone"]//div[contains(text(),"%s")]/../../div[@class="mdl-grid mdl-grid--nesting ssr-forms"]//option[contains(text()," %s ")]/@value'

insu_aquation_xpath = '//input[@id="remove_insurance_option"]/@name'

insu_qute_keys_xpath = '//div[@class="insurance-supplier-notes"]/../input/@name'

insu_qute_values_xpath = '//div[@class="insurance-supplier-notes"]/../input/@value'

final_price_xpath = '//div[@class="price-display-section price-display-section-total"]//div[@class="pull-right"]/text()'
