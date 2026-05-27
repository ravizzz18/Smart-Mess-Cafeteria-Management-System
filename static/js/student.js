document.addEventListener("DOMContentLoaded", () => {
    const qtyInputs = document.querySelectorAll(".qty-input");
    qtyInputs.forEach((input) => {
        input.addEventListener("change", () => {
            if (parseInt(input.value, 10) < 1) {
                input.value = 1;
            }
        });
    });
});
