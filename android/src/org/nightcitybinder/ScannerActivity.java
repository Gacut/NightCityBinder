package org.nightcitybinder;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.content.res.ColorStateList;
import android.graphics.Rect;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.FrameLayout;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Path;
import android.content.Context;
import android.widget.TextView;
import android.widget.ProgressBar;
import android.view.View;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.graphics.Insets;
import androidx.annotation.NonNull;
import androidx.activity.ComponentActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.content.ContextCompat;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import java.io.File;

/** Full-resolution local OCR. Camera frames never leave this device. */
public class ScannerActivity extends ComponentActivity {
    private PreviewView preview;
    private ImageCapture capture;
    private Button button;
    private boolean polish;
    private TextRecognizer recognizer;
    private ProcessCameraProvider provider;
    private File photo;
    private ProgressBar progress;

    @Override public void onCreate(Bundle state) {
        setTheme(android.R.style.Theme_Material_NoActionBar);
        super.onCreate(state);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        polish = "pl".equals(getIntent().getStringExtra("language"));
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(9, 7, 12));
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, window) -> {
            Insets bars = window.getInsets(WindowInsetsCompat.Type.systemBars()
                | WindowInsetsCompat.Type.displayCutout());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return window;
        });
        preview = new PreviewView(this);
        preview.setImplementationMode(PreviewView.ImplementationMode.COMPATIBLE);
        root.addView(preview, new FrameLayout.LayoutParams(-1, -1));
        CardGuide guide = new CardGuide(this);
        root.addView(guide, new FrameLayout.LayoutParams(-1, -1));

        TextView title = new TextView(this);
        title.setText(polish ? "Umieść kartę w ramce.\nZadbaj o ostry numer w lewym dolnym rogu."
            : "Place the card inside the frame.\nKeep the bottom-left number sharp.");
        title.setTextColor(Color.WHITE);
        title.setTextSize(14);
        title.setTypeface(Typeface.MONOSPACE);
        title.setGravity(Gravity.CENTER);
        title.setPadding(dp(12), dp(12), dp(12), dp(12));
        GradientDrawable titlePanel = new GradientDrawable();
        titlePanel.setColor(Color.argb(235, 22, 11, 17));
        titlePanel.setStroke(dp(1), Color.rgb(255, 82, 99));
        title.setBackground(titlePanel);
        FrameLayout.LayoutParams titleLayout = new FrameLayout.LayoutParams(-1, -2, Gravity.TOP);
        titleLayout.setMargins(dp(12), dp(12), dp(12), 0);
        root.addView(title, titleLayout);
        title.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, or, ob) -> {
            guide.reservedTop = b + dp(16) - root.getPaddingTop();
            guide.invalidate();
        });

        button = new Button(this);
        button.setTypeface(Typeface.MONOSPACE);
        button.setTextColor(new ColorStateList(new int[][]{new int[]{android.R.attr.state_enabled}, new int[]{}},
            new int[]{Color.rgb(92, 235, 242), Color.rgb(130, 100, 111)}));
        GradientDrawable actionPanel = new GradientDrawable();
        actionPanel.setColor(Color.rgb(22, 11, 17));
        actionPanel.setStroke(dp(1), Color.rgb(255, 82, 99));
        button.setBackground(actionPanel);
        button.setBackgroundTintList(null);
        button.setText(polish ? "Rozpoznaj kartę" : "Identify card");
        button.setEnabled(false);
        FrameLayout.LayoutParams buttonLayout = new FrameLayout.LayoutParams(-1, dp(56), Gravity.BOTTOM);
        buttonLayout.setMargins(dp(12), 0, dp(12), dp(8));
        root.addView(button, buttonLayout);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        progress.setIndeterminateTintList(ColorStateList.valueOf(Color.rgb(92, 235, 242)));
        FrameLayout.LayoutParams progressLayout = new FrameLayout.LayoutParams(-1, dp(6), Gravity.BOTTOM);
        progressLayout.setMargins(dp(12), 0, dp(12), dp(72));
        root.addView(progress, progressLayout);
        setContentView(root);
        button.setOnClickListener(v -> takePhoto());
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            startCamera();
        } else {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, 12);
        }
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    /** Visual positioning aid, not automatic card detection or an OCR crop. */
    private final class CardGuide extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path shade = new Path();
        private final RectF card = new RectF();
        int reservedTop = dp(112);

        CardGuide(Context context) { super(context); }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float top = reservedTop;
            float bottom = getHeight() - dp(92);
            float height = Math.max(0, Math.min(bottom - top, (getWidth() - dp(48)) * 88f / 63f));
            if (height <= 0) return;
            float width = height * 63f / 88f;
            float y = top + (bottom - top - height) / 2;
            card.set((getWidth() - width) / 2, y, (getWidth() + width) / 2, y + height);
            shade.reset();
            shade.setFillType(Path.FillType.EVEN_ODD);
            shade.addRect(0, 0, getWidth(), getHeight(), Path.Direction.CW);
            shade.addRoundRect(card, dp(2), dp(2), Path.Direction.CW);
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.argb(115, 0, 0, 0));
            canvas.drawPath(shade, paint);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(2));
            paint.setColor(Color.rgb(92, 235, 242));
            canvas.drawRoundRect(card, dp(2), dp(2), paint);
        }
    }

    @Override public void onRequestPermissionsResult(int request, @NonNull String[] permissions, @NonNull int[] grants) {
        super.onRequestPermissionsResult(request, permissions, grants);
        if (request == 12 && grants.length > 0 && grants[0] == PackageManager.PERMISSION_GRANTED) startCamera();
        else fail("camera_permission");
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> future = ProcessCameraProvider.getInstance(this);
        future.addListener(() -> {
            try {
                if (isFinishing() || isDestroyed()) return;
                provider = future.get();
                Preview view = new Preview.Builder().build();
                view.setSurfaceProvider(preview.getSurfaceProvider());
                capture = new ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY).build();
                provider.unbindAll();
                provider.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, view, capture);
                button.setEnabled(true);
                progress.setVisibility(View.INVISIBLE);
            } catch (Exception e) { fail("camera_unavailable"); }
        }, ContextCompat.getMainExecutor(this));
    }

    private void takePhoto() {
        if (capture == null) return;
        button.setEnabled(false);
        progress.setVisibility(View.VISIBLE);
        button.setText(polish ? "Rozpoznawanie…" : "Recognizing…");
        try { photo = File.createTempFile("scan-", ".jpg", getCacheDir()); }
        catch (Exception e) { fail("capture_failed"); return; }
        capture.setTargetRotation(preview.getDisplay().getRotation());
        capture.takePicture(new ImageCapture.OutputFileOptions.Builder(photo).build(),
            ContextCompat.getMainExecutor(this), new ImageCapture.OnImageSavedCallback() {
                @Override public void onImageSaved(@NonNull ImageCapture.OutputFileResults result) {
                    try {
                        if (isFinishing() || isDestroyed()) { photo.delete(); return; }
                        recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
                        InputImage image = InputImage.fromFilePath(ScannerActivity.this, Uri.fromFile(photo));
                        recognizer.process(image).addOnSuccessListener(text -> {
                            StringBuilder numbers = new StringBuilder();
                            int rotation = image.getRotationDegrees();
                            int width = rotation % 180 == 0 ? image.getWidth() : image.getHeight();
                            int height = rotation % 180 == 0 ? image.getHeight() : image.getWidth();
                            for (com.google.mlkit.vision.text.Text.TextBlock block : text.getTextBlocks()) {
                                for (com.google.mlkit.vision.text.Text.Line line : block.getLines()) {
                                    Rect bounds = line.getBoundingBox();
                                    if (bounds != null && bounds.left < width * 0.55f
                                            && bounds.centerY() > height * 0.65f) {
                                        numbers.append(line.getText()).append('\n');
                                    }
                                }
                            }
                            setResult(RESULT_OK, new Intent().putExtra("text", text.getText())
                                .putExtra("number_text", numbers.toString()));
                            finish();
                        }).addOnFailureListener(e -> fail("ocr_failed"))
                          .addOnCompleteListener(task -> { photo.delete(); recognizer.close(); });
                    } catch (Exception e) { fail("image_failed"); }
                }
                @Override public void onError(@NonNull ImageCaptureException error) { fail("capture_failed"); }
            });
    }

    private void fail(String error) {
        if (photo != null) photo.delete();
        setResult(RESULT_OK, new Intent().putExtra("error", error));
        finish();
    }

    @Override protected void onDestroy() {
        if (provider != null) provider.unbindAll();
        if (recognizer != null) recognizer.close();
        if (photo != null) photo.delete();
        super.onDestroy();
    }
}
