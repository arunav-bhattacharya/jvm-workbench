package workbench.startup.l03;

/** The depot's web API, as a client library would declare it. Don't change this interface. */
public interface DepotClient {
    String locate(String parcelId);
}
