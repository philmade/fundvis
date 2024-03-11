import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from sqlalchemy.orm import sessionmaker
from models import Institution, Funder, Author, Paper
from extensions import engine


from sqlalchemy.orm import joinedload


def fetch_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    authors = (
        session.query(Author)
        .options(joinedload(Author.institutions))
        .options(joinedload(Author.funders))
        .all()
    )
    session.close()
    return authors


def create_network_graph(authors):
    G = nx.Graph()
    for author in authors:
        author: Author
        G.add_node(author.name, type="author")
        for institution in author.institutions:
            institution: Institution
            G.add_node(institution.name, type="institution")
            G.add_edge(author.name, institution.name)
        for funder in author.funders:
            funder: Funder
            G.add_node(funder.name, type="funder")
            # print(f"Adding edge between {author.name} and {funder.name}")
            G.add_edge(author.name, funder.name)

    return G


def visualize_network(G):
    pos = nx.spring_layout(G)  # Position nodes using the spring layout
    fig, ax = plt.subplots(figsize=(12, 10))

    # Node colors and sizes based on type
    node_colors = {
        "author": "lightblue",
        "institution": "lightgreen",
        "funder": "salmon",
    }
    node_sizes = {"author": 100, "institution": 150, "funder": 200}

    for node_type in ["author", "institution", "funder"]:
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=[n for n in G.nodes if G.nodes[n]["type"] == node_type],
            node_size=node_sizes[node_type],
            node_color=node_colors[node_type],
            label=node_type,
            ax=ax,
        )

    # Draw edges with default styling
    nx.draw_networkx_edges(G, pos, edge_color="gray", ax=ax)

    # Draw labels for all nodes
    nx.draw_networkx_labels(G, pos, font_size=10, ax=ax)

    ax.axis("off")

    # Adding legend to distinguish node types
    ax.legend(scatterpoints=1)

    # Define hover callback function
    def on_hover(event):
        if event.inaxes != ax:
            return

        # Get the node closest to the mouse position
        xy = (event.xdata, event.ydata)
        node = min(
            pos.keys(),
            key=lambda n: ((pos[n][0] - xy[0]) ** 2 + (pos[n][1] - xy[1]) ** 2) ** 0.5,
        )
        node_type = G.nodes[node]["type"]

        if node_type == "author":
            # Display author information
            info = f"Author: {node}"
        elif node_type == "institution":
            # Display institution information
            info = f"Institution: {node}"
        elif node_type == "funder":
            # Display funder information
            info = f"Funder: {node}"

        # Display the information using Streamlit's st.info()
        st.info(info)

    # Connect the hover callback function to the figure for interactivity
    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    return fig


# Streamlit app
st.title("Author-Institution-Funder Network")

# Add search functionality
search_query = st.text_input("Search for authors, institutions, or funders")

authors = fetch_data()
for author in authors:
    for funder in author.funders:
        print(f"{author.name} - {funder.name}")
G = create_network_graph(authors)

if search_query:
    # Filter nodes based on the search query
    filtered_nodes = [
        node for node in G.nodes if search_query.lower() in str(node).lower()
    ]
    subgraph = G.subgraph(filtered_nodes)
    fig = visualize_network(subgraph)
else:
    fig = visualize_network(G)

st.pyplot(fig)
