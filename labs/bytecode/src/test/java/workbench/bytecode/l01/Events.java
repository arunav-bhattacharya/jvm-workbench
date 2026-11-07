package workbench.bytecode.l01;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Loaded by the app loader. Plugin copies in any loader write to this one shared log. */
public final class Events {
    public static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());

    private Events() {}
}
