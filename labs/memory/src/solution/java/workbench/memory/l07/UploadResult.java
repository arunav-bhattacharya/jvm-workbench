package workbench.memory.l07;

/** What the service answered: the thumbnail it made. A retry with the same upload id must get this same answer. */
public record UploadResult(String thumbnailId, String status, int width) {}
