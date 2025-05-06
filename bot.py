<html lang="en">
 <head>
  <meta charset="utf-8" />
  <meta content="width=device-width, initial-scale=1" name="viewport" />
  <title>Luxbyte Auth</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"
    rel="stylesheet"
  />
  <style>
    body {
      font-family: "Inter", sans-serif;
      margin: 0;
      padding: 0;
      background: linear-gradient(to top right, #2563eb, #7c3aed);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    #intro {
      position: fixed;
      inset: 0;
      background-color: #1e40af;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 50;
      color: #ffffff;
      font-weight: 700;
      font-size: 2.5rem;
      letter-spacing: 0.3em;
      user-select: none;
      animation: fadeOut 1s ease forwards;
      animation-delay: 3.5s;
    }
    #intro span {
      display: inline-block;
      opacity: 0;
      transform: scale(0.8);
      animation: popIn 0.5s forwards;
    }
    #intro span:nth-child(1) {
      animation-delay: 0s;
    }
    #intro span:nth-child(2) {
      animation-delay: 0.1s;
    }
    #intro span:nth-child(3) {
      animation-delay: 0.2s;
    }
    #intro span:nth-child(4) {
      animation-delay: 0.3s;
    }
    #intro span:nth-child(5) {
      animation-delay: 0.4s;
    }
    #intro span:nth-child(6) {
      animation-delay: 0.5s;
    }
    #intro span:nth-child(7) {
      animation-delay: 0.6s;
    }
    #intro span:nth-child(8) {
      animation-delay: 0.7s;
    }

    @keyframes popIn {
      to {
        opacity: 1;
        transform: scale(1);
      }
    }
    @keyframes fadeOut {
      to {
        opacity: 0;
        visibility: hidden;
      }
    }
    .card {
      background: white;
      border-radius: 1.5rem;
      box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
      max-width: 400px;
      width: 100%;
      padding: 2.5rem;
      position: relative;
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.8s ease, transform 0.8s ease;
    }
    .card.show {
      opacity: 1;
      transform: translateY(0);
    }
    .hidden {
      display: none;
    }
    .error-message {
      color: #dc2626;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }
    .success-message {
      color: #16a34a;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  </style>
 </head>
 <body>
  <div id="intro" aria-label="Luxbyte logo animation">
   <span>L</span><span>u</span><span>x</span><span>b</span><span>y</span><span>t</span><span>e</span>
  </div>

  <main aria-label="Authentication container" class="flex flex-col items-center w-full max-w-md gap-6">
   <!-- Login Card -->
   <section id="login-card" class="card show" aria-label="Login form">
    <h1 class="text-5xl font-extrabold text-indigo-700 select-none tracking-wide mb-6 text-center">
     Luxbyte
    </h1>
    <p class="mb-6 text-gray-500 font-medium text-center">
     Welcome back! Please login to your account.
    </p>
    <form id="login-form" class="space-y-6" novalidate>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="login-username">
       Phone number, username, or email
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="login-username"
        name="username"
        placeholder="Enter your username or email"
        type="text"
        autocomplete="username"
        required
      />
      <p id="login-username-error" class="error-message hidden"></p>
     </div>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="login-password">
       Password
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="login-password"
        name="password"
        placeholder="Enter your password"
        type="password"
        autocomplete="current-password"
        required
      />
      <p id="login-password-error" class="error-message hidden"></p>
     </div>
     <button
       id="login-submit"
       class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg shadow-md transition"
       type="submit"
     >
      Log In
     </button>
     <p id="login-error" class="error-message hidden text-center mt-2"></p>
     <p id="login-success" class="success-message hidden text-center mt-2"></p>
    </form>
    <div class="mt-6 text-center text-sm text-gray-600 font-semibold space-y-2 w-full">
     <button id="show-forgot" class="text-indigo-600 hover:underline block w-full" type="button">
      Forgot password?
     </button>
     <div>
      Don't have an account?
      <button id="show-signup" class="text-indigo-600 hover:underline ml-1" type="button">
       Sign up
      </button>
     </div>
    </div>
   </section>

   <!-- Signup Card -->
   <section id="signup-card" class="card hidden" aria-label="Sign up form">
    <h1 class="text-4xl font-extrabold text-indigo-700 select-none tracking-wide mb-6 text-center">
     Create Account
    </h1>
    <form id="signup-form" class="space-y-6" novalidate>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="signup-username">
       Username
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="signup-username"
        name="username"
        placeholder="Choose a username"
        type="text"
        required
      />
      <p id="signup-username-error" class="error-message hidden"></p>
     </div>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="signup-email">
       Email
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="signup-email"
        name="email"
        placeholder="Enter your email"
        type="email"
        required
      />
      <p id="signup-email-error" class="error-message hidden"></p>
     </div>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="signup-password">
       Password
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="signup-password"
        name="password"
        placeholder="Create a password"
        type="password"
        required
      />
      <p id="signup-password-error" class="error-message hidden"></p>
     </div>
     <button
       id="signup-submit"
       class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg shadow-md transition"
       type="submit"
     >
      Sign Up
     </button>
     <p id="signup-error" class="error-message hidden text-center mt-2"></p>
     <p id="signup-success" class="success-message hidden text-center mt-2"></p>
    </form>
    <div class="mt-6 text-center text-sm text-gray-600 font-semibold space-y-2 w-full">
     <button id="show-login-from-signup" class="text-indigo-600 hover:underline block w-full" type="button">
      Already have an account? Log in
     </button>
    </div>
   </section>

   <!-- Forgot Password Card -->
   <section id="forgot-card" class="card hidden" aria-label="Forgot password form">
    <h1 class="text-4xl font-extrabold text-indigo-700 select-none tracking-wide mb-6 text-center">
     Reset Password
    </h1>
    <form id="forgot-form" class="space-y-6" novalidate>
     <div>
      <label class="block text-sm font-semibold text-gray-700 mb-2" for="forgot-email">
       Email
      </label>
      <input
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-gray-700"
        id="forgot-email"
        name="email"
        placeholder="Enter your email"
        type="email"
        required
      />
      <p id="forgot-email-error" class="error-message hidden"></p>
     </div>
     <button
       id="forgot-submit"
       class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg shadow-md transition"
       type="submit"
     >
      Send Reset Link
     </button>
     <p id="forgot-error" class="error-message hidden text-center mt-2"></p>
     <p id="forgot-success" class="success-message hidden text-center mt-2"></p>
    </form>
    <div class="mt-6 text-center text-sm text-gray-600 font-semibold space-y-2 w-full">
     <button id="show-login-from-forgot" class="text-indigo-600 hover:underline block w-full" type="button">
      Back to Login
     </button>
    </div>
   </section>
  </main>

  <script>
    // Simple in-memory "database" for demo purposes
    const usersDB = JSON.parse(localStorage.getItem("luxbyteUsers") || "{}");

    // Save usersDB to localStorage
    function saveUsers() {
      localStorage.setItem("luxbyteUsers", JSON.stringify(usersDB));
    }

    // Show/hide cards
    const loginCard = document.getElementById("login-card");
    const signupCard = document.getElementById("signup-card");
    const forgotCard = document.getElementById("forgot-card");

    constshowCard = (card) => {
      [loginCard, signupCard, forgotCard].forEach((c) => {
        if (c === card) {
          c.classList.add("show");
          c.classList.remove("hidden");
        } else {
          c.classList.remove("show");
          c.classList.add("hidden");
        }
      });
    };

    // Intro animation
    window.addEventListener("DOMContentLoaded", () => {
      const intro = document.getElementById("intro");
      setTimeout(() => {
        intro.style.display = "none";
        loginCard.classList.add("show");
        loginCard.classList.remove("hidden");
      }, 4500);
    });

    // Navigation buttons
    document.getElementById("show-signup").addEventListener("click", () => {
      clearMessages();
      showCard(signupCard);
    });
    document.getElementById("show-login-from-signup").addEventListener("click", () => {
      clearMessages();
      showCard(loginCard);
    });
    document.getElementById("show-forgot").addEventListener("click", () => {
      clearMessages();
      showCard(forgotCard);
    });
    document.getElementById("show-login-from-forgot").addEventListener("click", () => {
      clearMessages();
      showCard(loginCard);
    });

    // Clear all error/success messages
    function clearMessages() {
      document.querySelectorAll(".error-message, .success-message").forEach((el) => {
        el.textContent = "";
        el.classList.add("hidden");
      });
    }

    // Validate email format
    function isValidEmail(email) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Validate username (simple: at least 3 chars)
    function isValidUsername(username) {
      return username.trim().length >= 3;
    }

    // Validate password (min 6 chars)
    function isValidPassword(password) {
      return password.length >= 6;
    }

    // LOGIN FORM
    const loginForm = document.getElementById("login-form");
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      clearMessages();

      const usernameInput = loginForm.username.value.trim();
      const passwordInput = loginForm.password.value;

      let valid = true;

      if (!usernameInput) {
        showError("login-username-error", "Username or email is required.");
        valid = false;
      }
      if (!passwordInput) {
        showError("login-password-error", "Password is required.");
        valid = false;
      }
      if (!valid) return;

      // Find user by username or email
      const user = Object.values(usersDB).find(
        (u) =>
          u.username.toLowerCase() === usernameInput.toLowerCase() ||
          u.email.toLowerCase() === usernameInput.toLowerCase()
      );

      if (!user) {
        showError("login-error", "User not found.");
        return;
      }
      if (user.password !== passwordInput) {
        showError("login-error", "Incorrect password.");
        return;
      }

      showSuccess("login-success", `Welcome back, ${user.username}!`);
      // Here you can redirect or do further actions after login
    });

    // SIGNUP FORM
    const signupForm = document.getElementById("signup-form");
    signupForm.addEventListener("submit", (e) => {
      e.preventDefault();
      clearMessages();

      const usernameInput = signupForm.username.value.trim();
      const emailInput = signupForm.email.value.trim();
      const passwordInput = signupForm.password.value;

      let valid = true;

      if (!isValidUsername(usernameInput)) {
        showError("signup-username-error", "Username must be at least 3 characters.");
        valid = false;
      }
      if (!isValidEmail(emailInput)) {
        showError("signup-email-error", "Please enter a valid email.");
        valid = false;
      }
      if (!isValidPassword(passwordInput)) {
        showError("signup-password-error", "Password must be at least 6 characters.");
        valid = false;
      }
      if (!valid) return;

      // Check if username or email already exists
      const usernameExists = Object.values(usersDB).some(
        (u) => u.username.toLowerCase() === usernameInput.toLowerCase()
      );
      const emailExists = Object.values(usersDB).some(
        (u) => u.email.toLowerCase() === emailInput.toLowerCase()
      );

      if (usernameExists) {
        showError("signup-username-error", "Username already taken.");
        return;
      }
      if (emailExists) {
        showError("signup-email-error", "Email already registered.");
        return;
      }

      // Save user
      usersDB[usernameInput.toLowerCase()] = {
        username: usernameInput,
        email: emailInput,
        password: passwordInput,
      };
      saveUsers();

      showSuccess("signup-success", "Account created successfully! You can now log in.");
      signupForm.reset();
    });

    // FORGOT PASSWORD FORM
    const forgotForm = document.getElementById("forgot-form");
    forgotForm.addEventListener("submit", (e) => {
      e.preventDefault();
      clearMessages();

      const emailInput = forgotForm.email.value.trim();

      if (!isValidEmail(emailInput)) {
        showError("forgot-email-error", "Please enter a valid email.");
        return;
      }

      // Check if email exists
      const user = Object.values(usersDB).find(
        (u) => u.email.toLowerCase() === emailInput.toLowerCase()
      );

      if (!user) {
        showError("forgot-error", "Email not found.");
        return;
      }

      // Simulate sending reset link
      showSuccess(
        "forgot-success",
        `A password reset link has been sent to ${emailInput}. (Simulation)`
      );
      forgotForm.reset();
    });

    // Helper functions to show messages
    function showError(id, message) {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = message;
        el.classList.remove("hidden");
      }
    }
    function showSuccess(id, message) {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = message;
        el.classList.remove("hidden");
      }
    }
  </script>
 </body>
</html>
