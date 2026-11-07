// version 1 of the hierarchy: two statuses
public sealed interface Status permits Active, Closed {}

record Active(String id) implements Status {}

record Closed(String id) implements Status {}
