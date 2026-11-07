package workbench.bytecode.l01.plugin;

import java.util.function.Supplier;
import workbench.bytecode.l01.Events;

/** A plugin class. Each loader that defines it gets its own statics. */
public class FxPlugin implements Supplier<String> {
    public static int INITS;

    static {
        INITS++;
        Events.LOG.add("FxPlugin init in " + FxPlugin.class.getClassLoader().getName());
    }

    @Override
    public String get() {
        return "rates from " + getClass().getClassLoader().getName();
    }
}
