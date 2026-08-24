% Draw a beautiful rose

% --- Petals: rose curve (polar) ---
theta = linspace(0, 2*pi, 1000);
n = 3;  % 3 petals for odd n
r = 2 * sin(n * theta);

% Convert to Cartesian
[xp, yp] = pol2cart(theta, r);

% Create a filled, smooth rose shape
figure('Color', 'white', 'Position', [200, 100, 550, 600]);
hold on;

% Draw petals with gradient effect
patch(xp, yp, [0.95 0.3 0.4], 'EdgeColor', [0.8 0.2 0.3], 'LineWidth', 1.5);

% Inner petals
r2 = 1.2 * sin(n * theta);
[xp2, yp2] = pol2cart(theta, r2);
patch(xp2, yp2, [0.98 0.5 0.55], 'EdgeColor', [0.85 0.35 0.4], 'LineWidth', 1);

% Innermost
r3 = 0.5 * sin(n * theta);
[xp3, yp3] = pol2cart(theta, r3);
patch(xp3, yp3, [1 0.7 0.75], 'EdgeColor', 'none');

% --- Stem ---
stem_x = [0, -0.15, -0.4, -0.8, -1.3, -1.9, -2.6, -3.3];
stem_y = [-2.2, -2.0, -1.9, -2.0, -2.3, -2.7, -3.2, -3.8];
plot(stem_x, stem_y, 'Color', [0.15 0.55 0.15], 'LineWidth', 3.5);

% --- Left leaf ---
leaf_x = [-0.8, -1.6, -2.2, -1.8, -0.8, -0.5];
leaf_y = [-2.0, -2.5, -2.1, -1.5, -1.2, -1.5];
patch(leaf_x, leaf_y, [0.2, 0.6, 0.2], 'EdgeColor', [0.1, 0.45, 0.1], 'LineWidth', 1);

% --- Right leaf ---
leaf2_x = [-1.5, -2.2, -2.8, -2.3, -1.5, -1.2];
leaf2_y = [-2.3, -1.8, -1.5, -1.9, -2.0, -2.1];
patch(leaf2_x, leaf2_y, [0.2, 0.6, 0.2], 'EdgeColor', [0.1, 0.45, 0.1], 'LineWidth', 1);

% --- Sepals ---
sepal_theta = linspace(pi/2, 3*pi/2, 200);
sepal_r = 0.3 + 0.05*sin(5*sepal_theta);
[sx, sy] = pol2cart(sepal_theta, sepal_r);
sy = sy - 2.2;
patch(sx, sy, [0.25 0.5 0.2], 'EdgeColor', 'none');

axis equal;
axis off;
title('🌹 Rose', 'FontSize', 18);

% Save
saveas(gcf, fullfile('E:\NEMT Simulator', 'rose_shape.png'));
hold off;

% Keep figure window open
uiwait(gcf);
