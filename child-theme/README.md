# child-theme

The **Divi child theme** — the only place custom theme code (PHP/CSS/JS) belongs.

- Keeps customizations upgrade-safe (the parent Divi theme is a licensed third-party product and is
  **not** committed here).
- Holds `functions.php` hooks, template parts, and any enqueue logic.
- The author-once site skeleton (header/footer/templates) is built with **Divi Theme Builder**;
  this child theme carries only the code that Theme Builder can't express.

> Divi itself is installed per-environment from the licensed Elegant Themes package — never vendored into Git.
