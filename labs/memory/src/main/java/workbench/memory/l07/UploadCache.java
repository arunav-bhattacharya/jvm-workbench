package workbench.memory.l07;

import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * Remembers the answer to each upload id. A phone on a weak connection often sends the same upload
 * twice, because it never heard the first answer, and the retry should get the same thumbnail back
 * instead of a second one.
 *
 * <p>In production this cache runs the service out of memory after a few days. Find what it keeps
 * alive and fix it. The cache must keep at most {@code maxEntries} entries, dropping the least
 * recently used one first, and it must keep rejecting a retry whose photo differs from the original,
 * without holding on to the photos.
 */
public final class UploadCache {
    private final int maxEntries;
    private final Map<String, Entry> entries = new ConcurrentHashMap<>();

    public UploadCache(int maxEntries) {
        this.maxEntries = maxEntries;
    }

    /**
     * Returns the result stored for the upload's id. For a new id, calls {@code handler} (which makes
     * the thumbnail), stores its result and returns it. Throws {@link UploadConflictException} when the
     * id was seen before with a different photo.
     */
    public UploadResult getOrCompute(PhotoUpload upload, Function<PhotoUpload, UploadResult> handler) {
        Entry seen = entries.get(upload.uploadId());
        if (seen != null) {
            if (!Arrays.equals(seen.upload().photo(), upload.photo())) {
                throw new UploadConflictException(upload.uploadId());
            }
            return seen.result();
        }
        UploadResult result = handler.apply(upload);
        entries.put(upload.uploadId(), new Entry(upload, result));
        return result;
    }

    /** How many results the cache holds. */
    public int size() {
        return entries.size();
    }

    private record Entry(PhotoUpload upload, UploadResult result) {}
}
