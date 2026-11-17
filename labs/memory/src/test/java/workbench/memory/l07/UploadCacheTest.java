package workbench.memory.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import javax.management.ObjectName;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UploadCacheTest {

    /** Live instances of a class, from the same class histogram `jcmd <pid> GC.class_histogram` prints. It runs a full GC first. */
    static long liveInstances(String className) throws Exception {
        String histogram = (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
                new Object[] {null}, new String[] {String[].class.getName()});
        for (String line : histogram.split("\n")) {
            String[] f = line.trim().split("\\s+");                 //    4:   20000   480000  workbench.memory.l07.UploadResult
            if (f.length >= 4 && f[3].equals(className)) return Long.parseLong(f[1]);
        }
        return 0;
    }

    /** Upload number n: a 2 KB stand-in for a photo, different for every n. */
    static PhotoUpload upload(int n) {
        byte[] photo = ("JPEG photo " + n + " " + "x".repeat(2_000)).getBytes(StandardCharsets.UTF_8);
        return new PhotoUpload("upload-" + n, "user-" + (n % 50), 160, photo);
    }

    static UploadResult makeThumbnail(PhotoUpload u) {
        return new UploadResult("thumb-" + u.uploadId(), "DONE", u.width());
    }

    @Test
    @DisplayName("a retry gets the stored result, and the thumbnail is made once")
    void retryGetsSameResult() {
        UploadCache cache = new UploadCache(100);
        AtomicInteger made = new AtomicInteger();
        UploadResult first = cache.getOrCompute(upload(1), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        UploadResult retry = cache.getOrCompute(upload(1), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        assertThat(retry).isEqualTo(first);
        assertThat(made.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("a retry that reuses the upload id with a different photo is rejected")
    void conflictingRetryIsRejected() {
        UploadCache cache = new UploadCache(100);
        cache.getOrCompute(upload(1), UploadCacheTest::makeThumbnail);
        PhotoUpload swapped = new PhotoUpload("upload-1", "user-1", 160, "a different photo".getBytes(StandardCharsets.UTF_8));
        assertThatThrownBy(() -> cache.getOrCompute(swapped, UploadCacheTest::makeThumbnail))
                .isInstanceOf(UploadConflictException.class);
    }

    @Test
    @DisplayName("the cache never holds more than maxEntries results")
    void bounded() {
        UploadCache cache = new UploadCache(500);
        for (int i = 0; i < 5_000; i++) cache.getOrCompute(upload(i), UploadCacheTest::makeThumbnail);
        assertThat(cache.size()).isEqualTo(500);
    }

    @Test
    @DisplayName("the least recently used entry is dropped first")
    void leastRecentlyUsedGoesFirst() {
        UploadCache cache = new UploadCache(2);
        AtomicInteger made = new AtomicInteger();
        cache.getOrCompute(upload(1), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        cache.getOrCompute(upload(2), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        cache.getOrCompute(upload(1), u -> { made.incrementAndGet(); return makeThumbnail(u); });   // 1 is now the most recent
        cache.getOrCompute(upload(3), u -> { made.incrementAndGet(); return makeThumbnail(u); });   // drops 2
        assertThat(made.get()).isEqualTo(3);
        cache.getOrCompute(upload(1), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        assertThat(made.get()).as("1 was still cached").isEqualTo(3);
        cache.getOrCompute(upload(2), u -> { made.incrementAndGet(); return makeThumbnail(u); });
        assertThat(made.get()).as("2 had been dropped, so the thumbnail was made again").isEqualTo(4);
    }

    @Test
    @DisplayName("after 20,000 uploads, no more than maxEntries results are still alive on the heap")
    void resultsDoNotPileUp() throws Exception {
        UploadCache cache = new UploadCache(500);
        for (int i = 0; i < 20_000; i++) cache.getOrCompute(upload(i), UploadCacheTest::makeThumbnail);
        assertThat(liveInstances("workbench.memory.l07.UploadResult")).isLessThanOrEqualTo(502);
        assertThat(cache.size()).isPositive();                   // keeps the cache reachable until the count is done
    }

    @Test
    @DisplayName("the cache keeps no upload, and so no photo, alive")
    void photosAreNotRetained() throws Exception {
        UploadCache cache = new UploadCache(500);
        for (int i = 0; i < 20_000; i++) cache.getOrCompute(upload(i), UploadCacheTest::makeThumbnail);
        assertThat(liveInstances("workbench.memory.l07.PhotoUpload")).isLessThanOrEqualTo(2);
        assertThat(cache.size()).isPositive();
    }
}
