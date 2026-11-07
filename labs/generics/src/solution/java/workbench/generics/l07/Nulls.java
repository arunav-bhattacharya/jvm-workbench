package workbench.generics.l07;

import java.util.List;

public final class Nulls {
    private Nulls() {}

    // List<?>: reads come out as Object, and only null could be added. No raw type, no warning.
    public static int countNulls(List<?> items) {
        int n = 0;
        for (Object item : items) if (item == null) n++;
        return n;
    }
}
