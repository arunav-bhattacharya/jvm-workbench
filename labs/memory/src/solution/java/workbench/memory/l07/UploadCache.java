package workbench.memory.l07;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;

public final class UploadCache {
    private final Map<String, Entry> entries;

    public UploadCache(int maxEntries) {
        // leak 1 fixed: a bound. accessOrder = true makes get() move an entry to the end,
        // so the eldest entry is the least recently used one, and removeEldestEntry drops it.
        this.entries = new LinkedHashMap<>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Entry> eldest) {
                return size() > maxEntries;
            }
        };
    }

    // synchronized: LinkedHashMap is not thread-safe, and even get() changes its order in access mode.
    // The lock also covers the handler, so two copies of a retry can't both make a thumbnail; a real
    // service would lock per upload id instead of for the whole cache.
    public synchronized UploadResult getOrCompute(PhotoUpload upload, Function<PhotoUpload, UploadResult> handler) {
        byte[] digest = sha256(upload.photo());
        Entry seen = entries.get(upload.uploadId());
        if (seen != null) {
            if (!MessageDigest.isEqual(seen.photoDigest(), digest)) {
                throw new UploadConflictException(upload.uploadId());
            }
            return seen.result();
        }
        UploadResult result = handler.apply(upload);
        entries.put(upload.uploadId(), new Entry(digest, result));
        return result;
    }

    public synchronized int size() {
        return entries.size();
    }

    // leak 2 fixed: keep a 32-byte fingerprint of the photo instead of the whole upload
    private record Entry(byte[] photoDigest, UploadResult result) {}

    private static byte[] sha256(byte[] photo) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(photo);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("every JDK has SHA-256", e);
        }
    }
}
