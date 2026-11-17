package workbench.performance.l07;

/** One document as it reaches the report service: a two-letter language code and a text of words separated by single spaces. */
public record Document(String id, String language, String text) { }
