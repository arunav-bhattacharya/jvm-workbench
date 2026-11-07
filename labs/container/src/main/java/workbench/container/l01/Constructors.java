package workbench.container.l01;

import java.lang.reflect.Constructor;

/** Chooses the one constructor the container calls for a component. */
public final class Constructors {
    private Constructors() {}

    /**
     * Look only at the public constructors ({@code type.getConstructors()}) that are not synthetic:
     * kotlinc adds a public synthetic one for default arguments.
     * <ol>
     *   <li>If exactly one is annotated {@link Inject}, return it. Two or more: throw
     *       {@code "<SimpleName> has 2 @Inject constructors; keep one"}.</li>
     *   <li>Otherwise, if there is exactly one, return it.</li>
     *   <li>None: throw {@code "<SimpleName> has no public constructor"}.</li>
     *   <li>Several: throw {@code "<SimpleName> has 2 public constructors; mark the one to use with @Inject"}.</li>
     * </ol>
     * Every failure is a {@link ContainerException}.
     */
    public static Constructor<?> pick(Class<?> type) {
        throw new UnsupportedOperationException("TODO: pick the @Inject constructor, or the only public one");
    }
}
