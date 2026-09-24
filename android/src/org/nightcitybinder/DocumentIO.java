package org.nightcitybinder;

import android.content.Context;
import android.content.ContentResolver;
import android.net.Uri;
import android.database.Cursor;
import android.provider.OpenableColumns;
import android.provider.DocumentsContract;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class DocumentIO {
    public static String name(Context context, Uri uri) {
        try (Cursor cursor = context.getContentResolver().query(uri,
                new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) return cursor.getString(0);
        }
        return uri.getLastPathSegment();
    }

    public static boolean delete(Context context, Uri uri) throws Exception {
        ContentResolver resolver = context.getContentResolver();
        if (DocumentsContract.isDocumentUri(context, uri)) {
            try {
                if (DocumentsContract.deleteDocument(resolver, uri) && !exists(resolver, uri)) {
                    return true;
                }
            } catch (UnsupportedOperationException ignored) {
                // Some document providers expose a URI but only implement delete().
            }
        }
        // Try the provider's ContentResolver.delete implementation as a fallback.
        return resolver.delete(uri, null, null) > 0 && !exists(resolver, uri);
    }

    private static boolean exists(ContentResolver resolver, Uri uri) {
        try (Cursor cursor = resolver.query(uri,
                new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            return cursor != null && cursor.moveToFirst();
        } catch (SecurityException | IllegalArgumentException ignored) {
            return false;
        }
    }
    public static String read(Context context, Uri uri) throws IOException {
        try (InputStream in = context.getContentResolver().openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            if (in == null) throw new IOException("No input stream");
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) {
                if (out.size() + count > 10000000) throw new IOException("File too large");
                out.write(buffer, 0, count);
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }
    public static void write(Context context, Uri uri, String text) throws IOException {
        try (OutputStream out = context.getContentResolver().openOutputStream(uri, "wt")) {
            if (out == null) throw new IOException("No output stream");
            out.write(text.getBytes(StandardCharsets.UTF_8));
        }
    }
}
