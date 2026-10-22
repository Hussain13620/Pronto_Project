<script type = py>
    import js
from pyscript import when
from pyodide.ffi import create_proxy

def is_logged_in():
    """Check if the user is logged in by reading localStorage."""
    return js.window.localStorage.getItem("loggedIn") == "true"

def redirect_book_service(event):
    """Redirect to services page if logged in, otherwise to login page."""
    event.preventDefault()
    if is_logged_in():
        js.window.location.href = "moksh_homeservices.html"
    else:
        js.window.location.href = "login.html"

@when("click", "#hero-book-btn")
def hero_book_click(event):
    redirect_book_service(event)

@when("click", "#audience-book-btn")
def audience_book_click(event):
    redirect_book_service(event)

def handle_service_card_click(event):
    """When a service card is clicked, redirect logged in user to booking_submission.html with service, else to login.html."""
    event.preventDefault()
    el = getattr(event, 'currentTarget', None)
    service_name = None
    if el and hasattr(el, 'getAttribute'):
        service_name = el.getAttribute("data-service")
    if not service_name:
        el = getattr(event, 'target', None)
        for _ in range(10):
            if el is None:
                break
            if hasattr(el, 'getAttribute') and el.getAttribute("data-service"):
                service_name = el.getAttribute("data-service")
                break
            el = getattr(el, 'parentElement', None)
    
    if service_name == "more":
        js.window.location.href = "moksh_homeservices.html"
    elif service_name:
        if is_logged_in():
            js.window.location.href = f"booking_submission.html?service={service_name}"
        else:
            js.window.location.href = "login.html"

service_card_proxy = create_proxy(handle_service_card_click)
cards = js.document.querySelectorAll(".services-grid .service-card")
for i in range(cards.length):
    cards[i].style.cursor = "pointer"
    cards[i].addEventListener("click", service_card_proxy)

# Update nav buttons based on login state
def handle_logout(event):
    event.preventDefault()
    js.window.localStorage.removeItem("loggedIn")
    js.window.localStorage.removeItem("userName")
    js.window.localStorage.removeItem("userType")
    js.window.location.reload()

def update_nav():
    if is_logged_in():
        nav_buttons = js.document.querySelector(".nav-buttons")
        if nav_buttons:
            nav_buttons.innerHTML = '<a href="#" id="logout-btn" class="signup-btn">Logout</a>'
            logout_btn = js.document.getElementById("logout-btn")
            if logout_btn:
                logout_proxy = create_proxy(handle_logout)
                logout_btn.addEventListener("click", logout_proxy)

update_nav()
</script>