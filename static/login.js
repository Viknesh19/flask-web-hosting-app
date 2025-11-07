document.getElementById('login-form').addEventListener('submit', function(e) {
    e.preventDefault();
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
  
    // Perform login validation here
    // You can use AJAX to send a request to the server for validation
  
    // Example validation
    if (username === 'user' && password === 'password') {
      alert('Login successful');
      // Redirect the user to a dashboard or home page
    } else {
      alert('Invalid username or password');
    }
  });
  
  document.getElementById('register-form').addEventListener('submit', function(e) {
    e.preventDefault();
    var username = document.getElementById('username').value;
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirm-password').value;
    var accountType = document.getElementById('account-type').value;
  
    // Perform registration validation here
    // You can use AJAX to send a request to the server for registration
  
    // Example validation
    if (password !== confirmPassword) {
      alert('Passwords do not match');
    } else {
      alert('Registration successful');
      // Redirect the user to a dashboard or home page
    }
  });
  