package org.nightcitybinder;

import android.app.Activity;
import android.view.View;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public final class SafeArea {
    /** Pixel overlap only: do not count space already excluded by Android/SDL. */
    public static int[] overlap(Activity activity) {
        View decor = activity.getWindow().getDecorView();
        View content = activity.findViewById(android.R.id.content);
        WindowInsetsCompat window = ViewCompat.getRootWindowInsets(decor);
        if (window == null || content == null) return new int[]{0, 0, 0, 0};
        Insets bars = window.getInsets(WindowInsetsCompat.Type.systemBars()
            | WindowInsetsCompat.Type.displayCutout());
        int[] d = new int[2], c = new int[2];
        decor.getLocationOnScreen(d);
        content.getLocationOnScreen(c);
        return new int[]{
            Math.max(0, d[0] + bars.left - c[0]),
            Math.max(0, d[1] + bars.top - c[1]),
            Math.max(0, c[0] + content.getWidth() - d[0] - decor.getWidth() + bars.right),
            Math.max(0, c[1] + content.getHeight() - d[1] - decor.getHeight() + bars.bottom)
        };
    }
}
