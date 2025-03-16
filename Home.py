import streamlit as st
import pandas as pd
import numpy as np
import time

st.subheader("Home 🏠​")
st.sidebar.subheader("Home🏠​")

st.text_input("Input", key="path-input")
st.text_input("Output", key="path-output")