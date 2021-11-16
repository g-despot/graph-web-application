import json
import logging
import os
from argparse import ArgumentParser
from flask import Flask, Response, render_template
from gqlalchemy import Memgraph

MEMGRAPH_HOST = os.getenv("MEMGRAPH_HOST", "memgraph-mage")
MEMGRAPH_PORT = int(os.getenv("MEMGRAPH_PORT", "7687"))

log = logging.getLogger(__name__)


def init_log():
    logging.basicConfig(level=logging.DEBUG)
    log.info("Logging enabled")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def parse_args():
    """
    Parse command line arguments.
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0", help="Host address.")
    parser.add_argument("--port", default=5000, type=int, help="App port.")
    parser.add_argument("--template-folder", default="public/template", help="Flask templates.")
    parser.add_argument("--static-folder", default="public", help="Flask static files.")
    parser.add_argument("--path-to-input-file", default="graph.cypherl", help="Graph input file.")
    parser.add_argument("--debug", default=True, action="store_true", help="Web server in debug mode.")
    print(__doc__)
    return parser.parse_args()


args = parse_args()
memgraph = None

app = Flask(
    __name__,
    template_folder=args.template_folder,
    static_folder=args.static_folder,
    static_url_path="",
)


def load_data(path_to_input_file):
    """Load data into the database."""
    try:
        node = memgraph.execute_and_fetch(
            "MATCH (n) RETURN n LIMIT 1;"
        )
        if len(list(node)) != 0:
            return
        memgraph.drop_database()
        with open(path_to_input_file, "r") as file:
            for line in file:
                memgraph.execute(line)
    except Exception as e:
        log.info(f"Data loading error: {e}")


def get_graph():
    results = memgraph.execute_and_fetch(
        f"""MATCH (c1:Character)-[k:KILLED]-(c2:Character)
                RETURN c1 as from, c2 AS to
                LIMIT 100;"""
    )
    return list(results)


@app.route("/get-graph", methods=["GET"])
def get_data():
    """Load everything from the database."""
    try:
        results = get_graph()

        # Set for quickly check if we have already added the node or the edge
        nodes_set = set()
        links_set = set()
        for result in results:
            source_id = result["from"].properties['name']
            target_id = result["to"].properties['name']

            nodes_set.add(source_id)
            nodes_set.add(target_id)

            if ((source_id, target_id) not in links_set and
                    (target_id, source_id,) not in links_set):
                links_set.add((source_id, target_id))

        nodes = [
            {"id": node_id}
            for node_id in nodes_set
        ]
        links = [{"source": n_id, "target": m_id} for (n_id, m_id) in links_set]

        response = {"nodes": nodes, "links": links}
        return Response(json.dumps(response), status=200, mimetype="application/json")
    except Exception as e:
        log.info(f"Data loading error: {e}")
        return ("", 500)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def main():
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        init_log()
        global memgraph
        memgraph = Memgraph(MEMGRAPH_HOST,
                            MEMGRAPH_PORT)
        load_data(args.path_to_input_file)
    app.run(host=args.host,
            port=args.port,
            debug=args.debug)


if __name__ == "__main__":
    main()
