import requests
import time

urls = {
    "huggingface_main": "https://huggingface.co",
    "huggingface_mirror": "https://hf-mirror.com"
}

def check_url(url):
    try:
        start_time = time.time()
        response = requests.head(url, timeout=5)  
        response_time = time.time() - start_time
        if response.status_code == 200:
            return True, response_time
        else:
            return False, None
    except requests.RequestException:
        return False, None

def choose_best_site():
    available_sites = {}
    
    main_status, main_time = check_url(urls["huggingface_main"])
    if main_status:
        available_sites["huggingface_main"] = main_time
    
    mirror_status, mirror_time = check_url(urls["huggingface_mirror"])
    if mirror_status:
        available_sites["huggingface_mirror"] = mirror_time
    
    if not available_sites:
        return "Error: Neither site is accessible", None, None
    
    best_site = min(available_sites, key=available_sites.get)
    return best_site, available_sites[best_site], urls[best_site]

if __name__ == "__main__":
    best_site, response_time, _ = choose_best_site()
    if isinstance(best_site, str) and "Error" in best_site:
        print(best_site)
    else:
        print(f"Best site: {best_site} with response time: {response_time:.4f} seconds, URL: {urls[best_site]}")
