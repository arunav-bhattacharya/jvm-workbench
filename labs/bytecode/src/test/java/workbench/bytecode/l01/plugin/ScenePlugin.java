package workbench.bytecode.l01.plugin;

import java.util.function.Supplier;
import workbench.bytecode.l01.Events;

/** A scene plugin for the show program. Each loader that defines it gets its own statics. */
public class ScenePlugin implements Supplier<String> {
    public static int INITS;

    static {
        INITS++;
        Events.LOG.add("ScenePlugin init in " + ScenePlugin.class.getClassLoader().getName());
    }

    @Override
    public String get() {
        return "scene from " + getClass().getClassLoader().getName();
    }
}
