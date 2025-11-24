document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("details").forEach((detail) => {
    detail.addEventListener("toggle", () => {
      if (detail.open) {
        document.querySelectorAll("details").forEach((other) => {
          if (other !== detail) {
            other.removeAttribute("open");
          }
        });
      }
    });
  });
});

