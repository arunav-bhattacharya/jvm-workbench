package workbench.startup.l02.fixtures;

/** The "application" a training run drives. Each kind of request touches different classes. */
public final class ParcelDesk {
    private ParcelDesk() {
    }

    public static String handle(String request) {
        if (request.startsWith("track")) {
            return Track.run(request);
        }
        if (request.startsWith("redirect")) {
            return Redirect.run(request);
        }
        return "unknown request";
    }
}
