% Draw a heart shape
t = linspace(0, 2*pi, 500);
x = 16 * sin(t).^3;
y = 13*cos(t) - 5*cos(2*t) - 2*cos(3*t) - cos(4*t);

figure('Color', 'white', 'Position', [300, 300, 500, 450]);
fill(x, y, 'r', 'EdgeColor', 'r', 'LineWidth', 2);
axis equal;
axis off;
title('Heart Shape', 'FontSize', 16);

% Save as image
saveas(gcf, fullfile(fileparts(mfilename('fullpath')), 'heart_shape.png'));

% Keep figure open
uiwait(gcf);
