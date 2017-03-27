import selenium, selenium.webdriver

class Plugin(object):
    def __init__(self, configuration):
        self.timeout = 10

        '''
        # NOTE : selenium.webdriver methods/properties
        add_cookie, application_cache, back, binary, capabilities, close,
        command_executor, create_web_element, current_url, current_window_handle, delete_all_cookies,
        delete_cookie, desired_capabilities, error_handler, execute, execute_async_script, execute_script,
        file_detector, file_detector_context, find_element, find_element_by_class_name, find_element_by_css_selector,
        find_element_by_id, find_element_by_link_text, find_element_by_name, find_element_by_partial_link_text,
        find_element_by_tag_name, find_element_by_xpath, find_elements, find_elements_by_class_name,
        find_elements_by_css_selector, find_elements_by_id, find_elements_by_link_text, find_elements_by_name,
        find_elements_by_partial_link_text, find_elements_by_tag_name, find_elements_by_xpath, firefox_profile,
        forward, get, get_cookie, get_cookies, get_log, get_screenshot_as_base64, get_screenshot_as_file,
        get_screenshot_as_png, get_window_position, get_window_size, implicitly_wait, log_types, maximize_window,
        mobile, name, options, orientation, page_source, profile, quit, refresh, save_screenshot, session_id,
        set_context, set_page_load_timeout, set_script_timeout, set_window_position, set_window_size, start_client,
        start_session, stop_client, switch_to, switch_to_active_element, switch_to_alert, switch_to_default_content,
        switch_to_frame, switch_to_window, title, w3c, window_handles
        '''

    def process(self, profile, state, vertex):
        if 'type' not in vertex:
            return { 'error' : "No vertex type defined!" }

        properties = dict()

        if vertex['type'] in [ 'url', 'domain' ]:

            url = vertex['id'].lower()
            if not url.startswith('http://') and not url.startswith('https://'):
                url = "http://" + url

            driver = selenium.webdriver.Firefox()
            driver.delete_all_cookies()
            driver.set_page_load_timeout(self.timeout)
            
            driver.set_window_size(800, 600)
            driver.set_window_position(0, 0)

            try:
                driver.get(url)
                properties['page_source'] = driver.page_source
                properties['title'] = driver.title
                properties['cookies'] = driver.get_cookies()
                properties['screenshot'] = driver.get_screenshot_as_base64()
            except:
                pass

            driver.close()

        return { "properties": properties, "neighbors" : [] }
