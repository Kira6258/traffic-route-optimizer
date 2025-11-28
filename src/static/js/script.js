document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('route-form');
    const submitBtn = document.getElementById('submit-btn');
    const errorDiv = document.getElementById('form-error');
    const inputs = form.querySelectorAll('input[type="text"]');

    // Client-side form validation
    form.addEventListener('submit', (e) => {
        let hasError = false;
        errorDiv.classList.add('hidden');
        errorDiv.textContent = '';

        inputs.forEach(input => {
            if (!input.value.trim()) {
                hasError = true;
                input.classList.add('border-red-500');
                errorDiv.textContent = 'Please fill in all fields.';
                errorDiv.classList.remove('hidden');
            } else {
                input.classList.remove('border-red-500');
            }
        });

        if (hasError) {
            e.preventDefault();
            submitBtn.disabled = true;
            setTimeout(() => { submitBtn.disabled = false; }, 2000);
        }
    });

    // Real-time input validation
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (input.value.trim()) {
                input.classList.remove('border-red-500');
                errorDiv.classList.add('hidden');
            }
        });
    });

    // Add loading state on form submission
    form.addEventListener('submit', () => {
        if (!errorDiv.textContent) {
            submitBtn.textContent = 'Generating...';
            submitBtn.disabled = true;
        }
    });
});