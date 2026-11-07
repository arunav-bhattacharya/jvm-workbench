// version 2: a third status, Frozen
public sealed interface Status permits Active, Closed, Frozen {}

record Active(String id) implements Status {}

record Closed(String id) implements Status {}

record Frozen(String id) implements Status {}
