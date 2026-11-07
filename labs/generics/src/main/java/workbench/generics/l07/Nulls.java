package workbench.generics.l07;

import java.util.List;

/** The Java side of "I don't know the element type": a raw type versus a wildcard. */
public final class Nulls {
    private Nulls() {}

    /**
     * Counts the null elements of {@code items}.
     *
     * <p>TODO: the parameter is a raw {@code List}. A raw type switches generic checking off, so this
     * method could add an Integer to someone's List&lt;String&gt; and nobody would notice until a read
     * far away. Change it to {@code List<?>} ("a list of some type I don't know"), then count the nulls.
     */
    @SuppressWarnings("rawtypes")
    public static int countNulls(List items) {
        throw new UnsupportedOperationException("TODO: use List<?>, then count the nulls");
    }
}
