package workbench.memory.l07;

/** A photo upload as the service received it. {@code photo} is the image file itself, a few kilobytes here. */
public record PhotoUpload(String uploadId, String userId, int width, byte[] photo) {}
