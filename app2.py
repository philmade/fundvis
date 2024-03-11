import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from sqlalchemy.orm import sessionmaker
from models import Institution, Funder, Author, Paper
from extensions import engine
import plotly.graph_objects as go

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


def fetch_author_via_paper_doi(doi):
    Session = sessionmaker(bind=engine)
    session = Session()
    author = (
        session.query(Author)
        .join(Author.papers)
        .filter(Paper.doi.in_(doi))
        .options(joinedload(Author.institutions))
        .options(joinedload(Author.funders))
        .all()
    )
    session.close()
    return author


def fetch_author_via_funder(funder):
    Session = sessionmaker(bind=engine)
    session = Session()
    author = (
        session.query(Author)
        .join(Author.funders)
        .filter(Funder.name.in_(funder))
        .options(joinedload(Author.institutions))
        .options(joinedload(Author.funders))
        .all()
    )
    session.close()
    return author


def fetch_doi():
    Session = sessionmaker(bind=engine)
    session = Session()
    doi = (
        session.query(Paper)
        .options(
            joinedload(Paper.doi), joinedload(Paper.authors), joinedload(Paper.funders)
        )
        .all()
    )
    session.close()
    return doi


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


def visualize_network_plotly(G):
    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        marker=dict(
            showscale=True,
            # color scale options
            # 'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu',
            # 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet',
            # 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'
            colorscale="YlGnBu",
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title="Node Connections",
                xanchor="left",
                titleside="right",
            ),
            line_width=2,
        ),
    )

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append("# of connections: " + str(len(adjacencies[1])))

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Python code generated network graph",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


def visualize_network_plotly(G):
    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    node_text = []
    node_size = []

    # Specify the size for each type of node
    sizes = {
        "funder": 25,
        "institution": 20,
        "author": 15,
    }

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # The node type is needed to determine the size of the node
        node_type = G.nodes[node]["type"]
        node_text.append(f"{node} ({node_type})")
        node_size.append(sizes[node_type])

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="bottom center",
        hoverinfo="text",
        marker=dict(
            showscale=False,
            colorscale="YlGnBu",
            reversescale=True,
            color=[],
            size=node_size,
            line_width=2,
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Python code generated network graph",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


def visualize_network_plotly(G):
    pos = nx.spring_layout(
        G
    )  # Force-directed layout simulating attractive/repulsive forces
    # pos = nx.kamada_kawai_layout(G)  # Force-directed layout based on path-length cost function
    # pos = nx.spectral_layout(
    #     G
    # )  # Layout based on the eigenvectors of the graph Laplacian
    # pos = nx.circular_layout(
    #     G
    # )  # Positions nodes uniformly around the circumference of a circle
    # pos = nx.random_layout(G)  # Positions nodes uniformly at random in the unit square
    # pos = nx.shell_layout(G)  # Positions nodes in concentric circles
    # pos = nx.bipartite_layout(G, nodes)  # Positions nodes in two straight lines
    # pos = nx.multipartite_layout(G)  # Positions nodes in straight lines by subsets
    # pos = nx.rescale_layout(G)  # Rescales an existing layout
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []

    # Define colors for each type of node
    colors = {
        "funder": "red",
        "institution": "orange",
        "author": "green",
    }

    # Define sizes for each type of node
    sizes = {
        "funder": 25,
        "institution": 20,
        "author": 15,
    }

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Get the node type
        node_type = G.nodes[node]["type"]

        # Update node text with the node's name
        node_text.append(f"{node} ({node_type})")

        # Assign node size based on type
        node_size.append(sizes[node_type])

        # Assign node color based on type
        node_color.append(colors[node_type])

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="bottom center",
        hoverinfo="text",
        marker=dict(
            size=node_size, color=node_color, line=dict(color="black", width=0.5)
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Network visualization",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=10000,
        ),
    )

    return fig


# Streamlit app
st.title("Author-Institution-Funder Network")

# Add search functionality
doi = st.text_input("Search for papers via DOI (comma separated)")
funder = st.text_input("Search for funders")


authors = fetch_data()
G = create_network_graph(authors)

if doi:
    if "," not in doi:
        doi += ","
    search_query = doi.split(",")
    authors = fetch_author_via_paper_doi(search_query)
    G = create_network_graph(authors)
    # Filter nodes based on the search query
    # filtered_nodes = [
    #     node for node in G.nodes if search_query.lower() in str(node).lower()
    # ]
    # subgraph = G.subgraph(filtered_nodes)
    fig = visualize_network_plotly(G)
if funder:
    if "," not in funder:
        funder += ","
    search_query = funder.split(",")
    authors = fetch_author_via_funder(search_query)
    G = create_network_graph(authors)
    fig = visualize_network_plotly(G)
else:
    fig = visualize_network_plotly(G)

st.plotly_chart(fig, use_container_width=True)
