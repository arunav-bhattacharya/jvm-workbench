package workbench.memory.l01;

/** Classes the tests measure. Predict each size before you run the tests. */
final class Samples {
    private Samples() {}

    /** The same fields as the JOL printout in the lesson. */
    static class Thumbnail {
        boolean cached;
        long createdAtMillis;
        byte format;
        String name;
        int width;
        byte[] pixels;
    }

    /** A subclass: its object holds Thumbnail's fields too. */
    static class WatermarkedThumbnail extends Thumbnail {
        String watermark;
        short opacity;
    }

    static class Upload {
        long sizeBytes;
        long uploadedAtMillis;
        String owner;
        char status;
    }

    /** Static fields live with the class, so they add nothing to each object. */
    static class ResizeRule {
        static final long MAX_PIXELS = 50_000_000;
        static int rulesLoaded;
        int targetWidth;
    }

    record PhotoId(long number, String album) {}
}
