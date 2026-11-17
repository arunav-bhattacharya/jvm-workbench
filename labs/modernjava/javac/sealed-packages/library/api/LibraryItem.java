package library.api;

// The sealed interface lives in library.api, its only permitted subtype in library.book.
// Compile it without module-info.java and javac refuses; compile it with module-info.java and it works.
public sealed interface LibraryItem permits library.book.Book {}
