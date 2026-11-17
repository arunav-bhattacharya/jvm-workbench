package workbench.memory.l07;

/** A client reused an upload id with a different photo. */
public class UploadConflictException extends RuntimeException {
    public UploadConflictException(String uploadId) {
        super("upload id reused with a different photo: " + uploadId);
    }
}
