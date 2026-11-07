package workbench.container.l01;

import java.lang.reflect.Constructor;
import java.util.Arrays;
import java.util.List;

/** Chooses the one constructor the container calls for a component. */
public final class Constructors {
    private Constructors() {}

    public static Constructor<?> pick(Class<?> type) {
        // kotlinc adds a public synthetic constructor for default arguments; it is not one the user wrote
        List<Constructor<?>> candidates = Arrays.stream(type.getConstructors())
                .filter(c -> !c.isSynthetic())
                .toList();
        List<Constructor<?>> marked = candidates.stream().filter(c -> c.isAnnotationPresent(Inject.class)).toList();
        if (marked.size() == 1) return marked.get(0);                 // 1. an explicit choice wins
        if (marked.size() > 1) {
            throw new ContainerException(type.getSimpleName() + " has " + marked.size() + " @Inject constructors; keep one");
        }
        if (candidates.size() == 1) return candidates.get(0);         // 2. the only public constructor
        if (candidates.isEmpty()) {
            throw new ContainerException(type.getSimpleName() + " has no public constructor");
        }
        // 3. never guess: getConstructors() returns them in no particular order
        throw new ContainerException(type.getSimpleName() + " has " + candidates.size()
                + " public constructors; mark the one to use with @Inject");
    }
}
