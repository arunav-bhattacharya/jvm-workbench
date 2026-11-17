package library.book;

public record Book(String isbn, String title) implements library.api.LibraryItem {}
